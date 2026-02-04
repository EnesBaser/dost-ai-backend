import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'handlers/achievement_handler.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'dart:async';
import '../../services/chat_service.dart';
import '../../services/chat_history_service.dart';
import '../../services/storage_service.dart';
import '../../services/notification_service.dart';
import '../../services/wake_word_service.dart';
import '../../services/achievements_service.dart' show Achievement, AchievementsService;
import '../../models/user_profile.dart';
import '../../models/message.dart';
import 'widgets/chat_app_bar.dart';
import 'widgets/chat_input_bar.dart';
import 'widgets/chat_message_list.dart';
import 'widgets/message_bubble.dart';
import 'widgets/empty_chat_view.dart';
import 'widgets/message_counter.dart';
import 'widgets/dost_avatar.dart';
import '../../services/greeting_service.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:easy_localization/easy_localization.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final ChatService _chatService = ChatService();
  final ChatHistoryService _chatHistoryService = ChatHistoryService();
  final StorageService _storageService = StorageService();
  final NotificationService _notificationService = NotificationService();
  final WakeWordService _wakeWordService = WakeWordService();
  final GreetingService _greetingService = GreetingService();
  final FlutterTts _flutterTts = FlutterTts();
  
  late AchievementHandler _achievementHandler; // DEĞIŞTI: late eklendi
  
  List<Message> _messages = [];
  UserProfile? _userProfile;
  bool _isLoading = false;
  bool _isListening = false;
  String _recognizedText = '';
  bool _isBackendHealthy = true;
  Timer? _backendHealthTimer;
  bool _wakeWordEnabled = false;
  bool _ttsEnabled = false;
  int _currentStreak = 0;
  int _todayMessageCount = 0;
  int _weekMessageCount = 0;
  int _totalMessageCount = 0;
  String? _proactiveMessage;
  AvatarEmotion _currentEmotion = AvatarEmotion.neutral;

  @override
  void initState() {
    super.initState();
    _achievementHandler = AchievementHandler(_chatHistoryService); // TAŞINDI: En üste
    _loadMessages();
    _loadUserProfile();
    _checkBackendHealth();
    _startBackendHealthCheck();
    _loadStreak();
    _initializeWakeWord();
    _loadMessageCounts();
    _checkProactiveMessage();
  }

  Future<void> _initializeWakeWord() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _wakeWordEnabled = prefs.getBool('wake_word_enabled') ?? false;
      _ttsEnabled = prefs.getBool('tts_enabled') ?? false;
    });

    if (_wakeWordEnabled) {
      // DEĞIŞTI: named parameter kullanıldı
      _wakeWordService.startListening(
        onWakeWordDetected: () {
          if (mounted) {
            _startListening();
          }
        },
      );
    }
  }

  Future<void> _toggleWakeWord() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _wakeWordEnabled = !_wakeWordEnabled;
    });
    await prefs.setBool('wake_word_enabled', _wakeWordEnabled);

    if (_wakeWordEnabled) {
      // DEĞIŞTI: named parameter kullanıldı
      _wakeWordService.startListening(
        onWakeWordDetected: () {
          if (mounted) {
            _startListening();
          }
        },
      );
    } else {
      await _wakeWordService.stopListening();
    }
  }

  Future<void> _toggleTTS() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _ttsEnabled = !_ttsEnabled;
    });
    await prefs.setBool('tts_enabled', _ttsEnabled);
  }

  Future<void> _loadStreak() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _currentStreak = prefs.getInt('current_streak') ?? 0;
    });
  }

  Future<void> _loadMessageCounts() async {
    final stats = await _chatHistoryService.getStatistics();
    final today = await _chatHistoryService.getTodayMessages();
    final week = await _chatHistoryService.getThisWeekMessages();
    
    setState(() {
      _todayMessageCount = today.where((m) => m['role'] == 'user').length;
      _weekMessageCount = week.where((m) => m['role'] == 'user').length;
      _totalMessageCount = stats['user'] ?? 0;
    });
  }

  Future<void> _checkProactiveMessage() async {
    if (_userProfile == null) return;
    
    // DEĞIŞTI: getRandomCheckIn kullanıldı
    final message = _greetingService.getRandomCheckIn();
    if (mounted) {
      setState(() {
        _proactiveMessage = message;
      });
    }
  }

  void _startBackendHealthCheck() {
    _backendHealthTimer = Timer.periodic(const Duration(seconds: 30), (timer) {
      _checkBackendHealth();
    });
  }

  Future<void> _checkBackendHealth() async {
    final isHealthy = await _chatService.checkHealth();
    if (mounted) {
      setState(() {
        _isBackendHealthy = isHealthy;
      });
    }
  }

  Future<void> _loadUserProfile() async {
    final profile = await _storageService.getUserProfile();
    setState(() {
      _userProfile = profile;
    });
  }

  Future<void> _loadMessages() async {
    // DEĞIŞTI: getAllMessages kullanıldı
    final allMessages = await _chatHistoryService.getAllMessages();
    final messages = allMessages.map((m) => Message(
      role: m['role'] as String,
      content: m['message'] as String,
      timestamp: DateTime.parse(m['timestamp'] as String),
    )).toList();
    
    setState(() {
      _messages = messages;
    });
  }

  Future<void> _sendMessage() async {
    final text = _messageController.text.trim();
    if (text.isEmpty || _isLoading) return;

    _messageController.clear();

    final userMessage = Message(
      role: 'user',
      content: text,
      timestamp: DateTime.now(),
    );

    setState(() {
      _messages.add(userMessage);
      _isLoading = true;
      _currentEmotion = AvatarEmotion.thinking;
    });

    // DEĞIŞTI: named parameters kullanıldı
    await _chatHistoryService.saveMessage(
      role: userMessage.role,
      message: userMessage.content,
      timestamp: userMessage.timestamp,
    );
    await _loadMessageCounts();

    try {
      final conversationHistory = _messages.map((m) => {
        'role': m.role,
        'content': m.content,
      }).toList();

      final response = await _chatService.sendMessage(
        message: text,
        conversationHistory: conversationHistory,
        userName: _userProfile?.displayName ?? 'Arkadaşım',
      );
	  print('🔥🔥🔥 RESPONSE: $response');

      if (response != null) {
        final aiMessage = Message(
          role: 'assistant',
          content: response,
          timestamp: DateTime.now(),
        );

        final emotion = _detectEmotion(response);
        
        setState(() {
          _messages.add(aiMessage);
          _currentEmotion = emotion;
        });

        // DEĞIŞTI: named parameters kullanıldı
        await _chatHistoryService.saveMessage(
          role: aiMessage.role,
          message: aiMessage.content,
          timestamp: aiMessage.timestamp,
        );
        await _speakMessage(response);
      }
    } catch (e) {
      print('Error sending message: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Mesaj gönderilemedi: $e')),
      );
    } finally {
      setState(() {
        _isLoading = false;
        if (_currentEmotion == AvatarEmotion.thinking) {
          _currentEmotion = AvatarEmotion.neutral;
        }
      });
    }

    // Başarım kontrolü
    await _achievementHandler.checkMessageAchievement(context);
  }

  AvatarEmotion _detectEmotion(String text) {
    final lowerText = text.toLowerCase();
    
    if (lowerText.contains('😊') || lowerText.contains('🎉') || 
        lowerText.contains('harika') || lowerText.contains('muhteşem') ||
        lowerText.contains('great') || lowerText.contains('awesome')) {
      return AvatarEmotion.happy;
    }
    
    if (lowerText.contains('😢') || lowerText.contains('üzgün') || 
        lowerText.contains('sad') || lowerText.contains('sorry')) {
      return AvatarEmotion.sad;
    }
    
    if (lowerText.contains('🤔') || lowerText.contains('?')) {
      return AvatarEmotion.thinking;
    }
    
    return AvatarEmotion.neutral;
  }

  Future<void> _speakMessage(String message) async {
    if (!_ttsEnabled) return;

    try {
      await _flutterTts.setLanguage("tr-TR");
      await _flutterTts.setPitch(1.0);
      await _flutterTts.setSpeechRate(0.5);
      await _flutterTts.speak(message);
    } catch (e) {
      print('TTS Error: $e');
    }
  }

  Future<void> _startListening() async {
    setState(() {
      _isListening = true;
      _recognizedText = '';
    });

    try {
      final result = await _chatService.startSpeechRecognition();
      if (result != null && result.isNotEmpty) {
        setState(() {
          _recognizedText = result;
          _messageController.text = result;
        });
        await _sendMessage();
      }
    } catch (e) {
      print('Speech recognition error: $e');
    } finally {
      setState(() {
        _isListening = false;
      });
    }

    // Ses başarımı
    await _achievementHandler.checkVoiceAchievement(context);
  }

  Future<void> _stopListening() async {
    await _chatService.stopSpeechRecognition();
    setState(() {
      _isListening = false;
    });
  }

  Future<void> _refreshMessages() async {
    await _loadMessages();
    await _loadMessageCounts();
    await _checkBackendHealth();
  }

  void _onFavoritesPress() async {
    final prefs = await SharedPreferences.getInstance();
    final favorites = prefs.getStringList('favorite_messages') ?? [];
    
    if (!mounted) return;
    
    if (favorites.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Henüz favori mesaj yok')),
      );
      return;
    }
    
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        expand: false,
        builder: (context, scrollController) => Container(
          decoration: const BoxDecoration(
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Favoriler',
                      style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                    ),
                    Text(
                      '${favorites.length} mesaj',
                      style: const TextStyle(color: Colors.grey),
                    ),
                  ],
                ),
              ),
              const Divider(height: 1),
              Expanded(
                child: ListView.builder(
                  controller: scrollController,
                  itemCount: favorites.length,
                  itemBuilder: (context, index) {
                    final message = favorites[index];
                    return ListTile(
                      leading: const Icon(Icons.star, color: Colors.amber),
                      title: Text(
                        message,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      trailing: IconButton(
                        icon: const Icon(Icons.delete, color: Colors.red),
                        onPressed: () async {
                          favorites.removeAt(index);
                          await prefs.setStringList('favorite_messages', favorites);
                          Navigator.pop(context);
                          _onFavoritesPress(); // Refresh
                        },
                      ),
                      onTap: () {
                        Clipboard.setData(ClipboardData(text: message));
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Mesaj kopyalandı')),
                        );
                      },
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  int _getFavoritesCount() {
    // This will be updated after first favorites load
    return 0; // Real-time count will be shown in AppBar via state
  }
  
  Future<void> _updateFavoritesCount() async {
    final prefs = await SharedPreferences.getInstance();
    final favorites = prefs.getStringList('favorite_messages') ?? [];
    if (mounted) {
      setState(() {
        // Update via AppBar rebuild
      });
    }
  }

  void _onMessageLongPress(String message, int index) {
    showModalBottomSheet(
      context: context,
      builder: (context) => Container(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.copy),
              title: const Text('Kopyala'),
              onTap: () async {
                await Clipboard.setData(ClipboardData(text: message));
                Navigator.pop(context);
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Mesaj kopyalandı')),
                  );
                }
              },
            ),
            ListTile(
              leading: const Icon(Icons.star),
              title: const Text('Favorilere Ekle'),
              onTap: () async {
                final prefs = await SharedPreferences.getInstance();
                final favorites = prefs.getStringList('favorite_messages') ?? [];
                
                if (!favorites.contains(message)) {
                  favorites.add(message);
                  await prefs.setStringList('favorite_messages', favorites);
                  
                  Navigator.pop(context);
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Favorilere eklendi')),
                    );
                  }
                } else {
                  Navigator.pop(context);
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Zaten favorilerde')),
                    );
                  }
                }
              },
            ),
            ListTile(
              leading: const Icon(Icons.delete),
              title: const Text('Sil'),
              onTap: () async {
                Navigator.pop(context);
                
                final confirm = await showDialog<bool>(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: const Text('Mesajı Sil'),
                    content: const Text('Bu mesajı silmek istediğinize emin misiniz?'),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(context, false),
                        child: const Text('İptal'),
                      ),
                      TextButton(
                        onPressed: () => Navigator.pop(context, true),
                        child: const Text('Sil', style: TextStyle(color: Colors.red)),
                      ),
                    ],
                  ),
                );
                
                if (confirm == true && mounted) {
                  setState(() {
                    _messages.removeAt(index);
                  });
                  
                  // Database'den de sil
                  await _chatHistoryService.deleteMessage(index);
                  
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Mesaj silindi')),
                    );
                  }
                }
              },
            ),
          ],
        ),
      ),
    );
  }

  // SİLİNDİ: _checkAndShowAchievement ve _checkVoiceAchievement (AchievementHandler kullanıyoruz)
  // SİLİNDİ: _showAchievementDialog (AchievementDialog kullanıyoruz)

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    _flutterTts.stop();
    // SİLİNDİ: _wakeWordService.dispose() çünkü metod yok
    _backendHealthTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: ChatAppBar(
        userProfile: _userProfile,
        isBackendHealthy: _isBackendHealthy,
        wakeWordEnabled: _wakeWordEnabled,
        ttsEnabled: _ttsEnabled,
        currentStreak: _currentStreak,
		currentEmotion: _currentEmotion,
        favoritesCount: _getFavoritesCount(),
        messages: _messages.map((m) => <String, dynamic>{
          'role': m.role,
          'message': m.content,
          'timestamp': m.timestamp,
        }).toList(),
        onWakeWordToggle: _toggleWakeWord,
        onTTSToggle: _toggleTTS,
        onRefresh: _refreshMessages,
        onFavoritesPress: _onFavoritesPress,
      ),
      body: Column(
        children: [
          Expanded(
            child: _messages.isEmpty
                ? EmptyChatView(
                    userProfile: _userProfile,
                    proactiveMessage: _proactiveMessage,
                    greetingService: _greetingService,
                  )
                : ChatMessageList(
                    messages: _messages.map((m) => {
                      'role': m.role,
                      'message': m.content,
                      'timestamp': m.timestamp,
                    }).toList(),
                    scrollController: _scrollController,
                    onMessageLongPress: _onMessageLongPress,
                  ),
          ),
          MessageCounter(
            todayCount: _todayMessageCount,
            weekCount: _weekMessageCount,
            totalCount: _totalMessageCount,
          ),
          ChatInputBar(
            messageController: _messageController,
            isListening: _isListening,
            isLoading: _isLoading,
            onSend: _sendMessage,
            onStartListening: _startListening,
            onStopListening: _stopListening,
          ),
        ],
      ),
    );
  }
}