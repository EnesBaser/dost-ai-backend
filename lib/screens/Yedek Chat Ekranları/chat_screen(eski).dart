import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';
import '../models/user_profile.dart';
import 'profile_screen.dart';
import '../services/speech_service.dart';
import '../services/greeting_service.dart';
import '../services/emotion_service.dart';      // YENİ
import '../services/special_days_service.dart';  // YENİ
import '../services/chat_history_service.dart';
import 'search_screen.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<Map<String, dynamic>> _messages = [];
  final ApiService _apiService = ApiService();
  final StorageService _storageService = StorageService();
  final SpeechService _speechService = SpeechService();
  final GreetingService _greetingService = GreetingService();
  final EmotionService _emotionService = EmotionService();           // YENİ
  final SpecialDaysService _specialDaysService = SpecialDaysService(); // YENİ
  final ChatHistoryService _chatHistoryService = ChatHistoryService();
  
  bool _isLoading = false;
  bool _isBackendHealthy = false;
  bool _isListening = false;
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
  Future<void> _checkSpecialDays() async {
    final birthdayMessage = await _specialDaysService.getBirthdayMessage();
    
    if (birthdayMessage != null) {
      setState(() {
        _proactiveMessage = birthdayMessage;
      });
    }
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
    // Son görülme kontrolü
    final prefs = await SharedPreferences.getInstance();
    final lastSeenString = prefs.getString('last_seen');
    DateTime? lastSeen;
    
    if (lastSeenString != null) {
      lastSeen = DateTime.parse(lastSeenString);
    }

    setState(() {
      // Önce "seni özledim" mesajını kontrol et
      _proactiveMessage = _greetingService.getMissYouMessage(lastSeen);
      
      // Yoksa hafta sonu mesajı
      _proactiveMessage ??= _greetingService.getWeekendMessage();
      
      // Yoksa rastgele check-in
      _proactiveMessage ??= _greetingService.getRandomCheckIn();
    });
  }

  Future<void> _updateLastSeen() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('last_seen', DateTime.now().toIso8601String());
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

    // Duygu analizi yap
    final emotionAnalysis = _emotionService.analyzeEmotion(message);
    final emotion = emotionAnalysis['emotion'] as String;

    // Kullanıcı bilgilerini gönder
    final response = await _apiService.sendMessage(
      message,
      userName: _userProfile?.displayName,
      interests: _userProfile?.interests,
	  emotion: emotion,
    );

    setState(() {
      _messages.add({
        'role': 'assistant',
        'message': response,
        'timestamp': DateTime.now().toUtc().add(const Duration(hours: 3)),
      });
      
      // Eğer olumsuz duygu varsa, destek mesajı ekle
      if (emotion == 'sad' && emotionAnalysis['negativeScore'] > 2) {
        _messages.add({
          'role': 'assistant',
          'message': _emotionService.getEmotionalResponse(emotion),
          'timestamp': DateTime.now().toUtc().add(const Duration(hours: 3)),
        });
      }
      
      _isLoading = false;
    });

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
          // Mesaj listesi
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
                      
                      return Align(
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
                                : Colors.grey[300],
                            borderRadius: BorderRadius.circular(15),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                msg['message']!,
                                style: TextStyle(
                                  color: isUser ? Colors.white : Colors.black,
                                  fontSize: 15,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                timeStr,
                                style: TextStyle(
                                  color: isUser ? Colors.white70 : Colors.black54,
                                  fontSize: 11,
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),

          // Loading indicator
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.all(8.0),
              child: CircularProgressIndicator(),
            ),

          // Mesaj giriş alanı
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: Colors.white,
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
                // Mikrofon butonu
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
                Expanded(
                  child: TextField(
                    controller: _messageController,
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