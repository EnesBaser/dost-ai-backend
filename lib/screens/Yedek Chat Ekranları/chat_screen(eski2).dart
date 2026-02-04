import 'package:flutter/material.dart';
import '../services/tts_service.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';
import '../models/user_profile.dart';
import 'profile_screen.dart';
import '../services/speech_service.dart';
import '../services/greeting_service.dart';
import '../services/emotion_service.dart';
import '../services/special_days_service.dart';
import '../services/chat_history_service.dart';
import 'search_screen.dart';
import '../widgets/typing_indicator.dart';
import '../widgets/wave_animation.dart';
import '../services/wake_word_service.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final TTSService _ttsService = TTSService();
  final ScrollController _scrollController = ScrollController();
  final List<Map<String, dynamic>> _messages = [];
  final ApiService _apiService = ApiService();
  final StorageService _storageService = StorageService();
  final SpeechService _speechService = SpeechService();
  final GreetingService _greetingService = GreetingService();
  final EmotionService _emotionService = EmotionService();
  final SpecialDaysService _specialDaysService = SpecialDaysService();
  final ChatHistoryService _chatHistoryService = ChatHistoryService();
  final WakeWordService _wakeWordService = WakeWordService();
  
  bool _isTTSEnabled = false;
  bool _isLoading = false;
  bool _isBackendHealthy = false;
  bool _isListening = false;
  bool _wakeWordEnabled = false;
  UserProfile? _userProfile;
  String? _proactiveMessage;

  @override
  void initState() {
    super.initState();
    _loadUserProfile();
    _checkBackendHealth();
    _loadProactiveMessage();
    _updateLastSeen();
    _checkSpecialDays();
  }

  Future<void> _loadUserProfile() async {
    final profile = await _storageService.getUserProfile();
    setState(() {
      _userProfile = profile;
    });
  }

  Future<void> _checkBackendHealth() async {
    final healthy = await _apiService.checkHealth();
    setState(() {
      _isBackendHealthy = healthy;
    });
  }

  Future<void> _loadProactiveMessage() async {
    final prefs = await SharedPreferences.getInstance();
    final lastSeenString = prefs.getString('last_seen');
    DateTime? lastSeen;
    
    if (lastSeenString != null) {
      lastSeen = DateTime.parse(lastSeenString);
    }

    setState(() {
      _proactiveMessage = _greetingService.getMissYouMessage(lastSeen);
      _proactiveMessage ??= _greetingService.getWeekendMessage();
      _proactiveMessage ??= _greetingService.getRandomCheckIn();
    });
  }

  Future<void> _updateLastSeen() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('last_seen', DateTime.now().toIso8601String());
  }

  Future<void> _checkSpecialDays() async {
    final birthdayMessage = await _specialDaysService.getBirthdayMessage();
    
    if (birthdayMessage != null) {
      setState(() {
        _proactiveMessage = birthdayMessage;
      });
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage() async {
    final message = _messageController.text.trim();
    if (message.isEmpty) return;

    final now = DateTime.now().toUtc().add(const Duration(hours: 3));

    setState(() {
      _messages.add({
        'role': 'user',
        'message': message,
        'timestamp': now,
      });
      _isLoading = true;
    });

    await _chatHistoryService.saveMessage(
      role: 'user',
      message: message,
      timestamp: now,
    );

    _messageController.clear();
    _scrollToBottom();

    final emotionAnalysis = _emotionService.analyzeEmotion(message);
    final emotion = emotionAnalysis['emotion'] as String;

    final response = await _apiService.sendMessage(
      message,
      userName: _userProfile?.displayName,
      interests: _userProfile?.interests,
      emotion: emotion,
    );

    final aiTimestamp = DateTime.now().toUtc().add(const Duration(hours: 3));

    setState(() {
      _messages.add({
        'role': 'assistant',
        'message': response,
        'timestamp': aiTimestamp,
      });
      
      if (emotion == 'sad' && emotionAnalysis['negativeScore'] > 2) {
        _messages.add({
          'role': 'assistant',
          'message': _emotionService.getEmotionalResponse(emotion),
          'timestamp': DateTime.now().toUtc().add(const Duration(hours: 3)),
        });
      }
      
      _isLoading = false;
    });

    await _chatHistoryService.saveMessage(
      role: 'assistant',
      message: response,
      timestamp: aiTimestamp,
    );

    _scrollToBottom();
  }

  Future<void> _startListening() async {
    setState(() => _isListening = true);
    
    await _speechService.startListening(
      onResult: (text) {
        _messageController.text = text;
      },
      onListeningComplete: () {
        setState(() => _isListening = false);
      },
    );
  }

  Future<void> _stopListening() async {
    await _speechService.stopListening();
    setState(() => _isListening = false);
  }

  void _onWakeWordDetected() {
    print('🎤 Wake word algılandı!');
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Dinliyorum! 👋'),
        duration: Duration(seconds: 1),
      ),
    );
    _startListening();
  }

  Future<void> _toggleWakeWord() async {
    await _wakeWordService.toggle(
      onWakeWordDetected: _onWakeWordDetected,
    );
    setState(() {
      _wakeWordEnabled = _wakeWordService.isEnabled;
    });
  }

  void _showMessageOptions(BuildContext context, String message, int index) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _buildReactionButton(context, '❤️', index),
                    _buildReactionButton(context, '👍', index),
                    _buildReactionButton(context, '😊', index),
                    _buildReactionButton(context, '🎉', index),
                    _buildReactionButton(context, '🔥', index),
                  ],
                ),
              ),
              const Divider(),
              ListTile(
                leading: const Icon(Icons.copy),
                title: const Text('Kopyala'),
                onTap: () {
                  Clipboard.setData(ClipboardData(text: message));
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Mesaj kopyalandı!'),
                      duration: Duration(seconds: 1),
                    ),
                  );
                },
              ),
              ListTile(
                leading: const Icon(Icons.delete_outline, color: Colors.red),
                title: const Text('Sil', style: TextStyle(color: Colors.red)),
                onTap: () {
                  Navigator.pop(context);
                  // Onay dialogu göster
                  showDialog(
                    context: context,
                    builder: (dialogContext) => AlertDialog(
                      title: const Text('Mesajı Sil'),
                      content: const Text('Bu mesajı silmek istediğinize emin misiniz?'),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(dialogContext),
                          child: const Text('İptal'),
                        ),
                        TextButton(
                          onPressed: () {
                            Navigator.pop(dialogContext);
                            setState(() {
                              _messages.removeAt(index);
                            });
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('Mesaj silindi 🗑️'),
                                duration: Duration(seconds: 2),
                              ),
                            );
                          },
                          style: TextButton.styleFrom(foregroundColor: Colors.red),
                          child: const Text('Sil'),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildReactionButton(BuildContext context, String emoji, int index) {
    return GestureDetector(
      onTap: () {
        Navigator.pop(context);
        setState(() {
          _messages[index]['reaction'] = emoji;
        });
      },
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.grey[200],
          shape: BoxShape.circle,
        ),
        child: Text(
          emoji,
          style: const TextStyle(fontSize: 24),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.deepPurple,
        foregroundColor: Colors.white,
        title: Row(
          children: [
            Text(_userProfile != null 
                ? 'Dost AI - ${_userProfile!.displayName}' 
                : 'Dost AI'),
            const SizedBox(width: 10),
            Container(
              width: 10,
              height: 10,
              decoration: BoxDecoration(
                color: _isBackendHealthy ? Colors.green : Colors.red,
                shape: BoxShape.circle,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(
              _wakeWordEnabled ? Icons.hearing : Icons.hearing_disabled,
              color: _wakeWordEnabled ? Colors.green : Colors.white,
            ),
            onPressed: _toggleWakeWord,
            tooltip: _wakeWordEnabled ? 'Hey Dost: Açık' : 'Hey Dost: Kapalı',
          ),
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (context) => const SearchScreen(),
                ),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.person),
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (context) => ProfileScreen(),
                ),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _checkBackendHealth,
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _messages.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          _userProfile != null
                              ? _greetingService.getTimeBasedGreeting(_userProfile!.displayName)
                              : 'Merhaba! Ben Dost AI.',
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: Colors.deepPurple,
                          ),
                        ),
                        const SizedBox(height: 20),
                        if (_proactiveMessage != null) ...[
                          Container(
                            margin: const EdgeInsets.symmetric(horizontal: 40),
                            padding: const EdgeInsets.all(15),
                            decoration: BoxDecoration(
                              color: Colors.deepPurple.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(15),
                              border: Border.all(
                                color: Colors.deepPurple.withOpacity(0.3),
                              ),
                            ),
                            child: Text(
                              _proactiveMessage!,
                              textAlign: TextAlign.center,
                              style: const TextStyle(
                                fontSize: 16,
                                color: Colors.deepPurple,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                  )
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(10),
                    itemCount: _messages.length,
                    itemBuilder: (context, index) {
                      final msg = _messages[index];
                      final isUser = msg['role'] == 'user';
                      final timestamp = msg['timestamp'] as DateTime;
                      final timeStr = DateFormat('HH:mm').format(timestamp);
                      
                      return GestureDetector(
                        onLongPress: () {
                          _showMessageOptions(context, msg['message'], index);
                        },
                        child: Align(
                          alignment: isUser
                              ? Alignment.centerRight
                              : Alignment.centerLeft,
                          child: Container(
                            margin: const EdgeInsets.symmetric(vertical: 5),
                            padding: const EdgeInsets.all(12),
                            constraints: BoxConstraints(
                              maxWidth: MediaQuery.of(context).size.width * 0.7,
                            ),
                            decoration: BoxDecoration(
                              color: isUser
                                  ? Colors.deepPurple
                                  : (Theme.of(context).brightness == Brightness.dark
                                      ? const Color(0xFF2C2C2C)
                                      : Colors.grey[300]),
                              borderRadius: BorderRadius.circular(15),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  msg['message']!,
                                  style: TextStyle(
                                    color: isUser 
                                        ? Colors.white 
                                        : (Theme.of(context).brightness == Brightness.dark
                                            ? Colors.white
                                            : Colors.black),
                                    fontSize: 15,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Text(
                                      timeStr,
                                      style: TextStyle(
                                        color: isUser ? Colors.white70 : Colors.black54,
                                        fontSize: 11,
                                      ),
                                    ),
                                    if (msg['reaction'] != null) ...[
                                      const SizedBox(width: 8),
                                      Text(
                                        msg['reaction'],
                                        style: const TextStyle(fontSize: 16),
                                      ),
                                    ],
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
          ),

          if (_isLoading)
            const TypingIndicator(),

          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: Theme.of(context).brightness == Brightness.dark
                  ? const Color(0xFF1E1E1E)
                  : Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.grey.withOpacity(0.3),
                  blurRadius: 5,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: Row(
              children: [
                CircleAvatar(
                  backgroundColor: _isListening ? Colors.red : Colors.grey[300],
                  child: IconButton(
                    icon: Icon(
                      _isListening ? Icons.mic : Icons.mic_none,
                      color: _isListening ? Colors.white : Colors.grey[700],
                    ),
                    onPressed: _isListening ? _stopListening : _startListening,
                  ),
                ),
                const SizedBox(width: 10),
                if (_isListening)
                  const Expanded(
                    child: WaveAnimation(),
                  ),
                if (!_isListening)
                  Expanded(
                    child: TextField(
                      controller: _messageController,
                      style: TextStyle(
                        color: Theme.of(context).brightness == Brightness.dark
                            ? Colors.white
                            : Colors.black,
                      ),
                      decoration: InputDecoration(
                        hintText: _isListening ? 'Dinliyorum...' : 'Mesajını yaz...',
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(25),
                        ),
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 20,
                          vertical: 10,
                        ),
                      ),
                      onSubmitted: (_) => _sendMessage(),
                      enabled: !_isListening,
                    ),
                  ),
                const SizedBox(width: 10),
                CircleAvatar(
                  backgroundColor: Colors.deepPurple,
                  child: IconButton(
                    icon: const Icon(Icons.send, color: Colors.white),
                    onPressed: _isLoading || _isListening ? null : _sendMessage,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}