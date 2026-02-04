import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:speech_to_text/speech_to_text.dart' as stt;

class ChatService {
  static const String baseUrl = 'http://192.168.2.109:5001';
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isListening = false;
  String _recognizedText = '';

  Future<bool> checkHealth() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/health')).timeout(
        const Duration(seconds: 5),
      );
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  Future<String?> sendMessage({
    required String message,
    required List<Map<String, dynamic>> conversationHistory,
    required String userName,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/chat'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'message': message,
          'conversation_history': conversationHistory,
          'user_name': userName,
        }),
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['response'];
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  Future<String?> startSpeechRecognition() async {
    try {
      bool available = await _speech.initialize();
      if (!available) return null;
      _isListening = true;
      _recognizedText = '';
      await _speech.listen(
        onResult: (result) {
          _recognizedText = result.recognizedWords;
        },
        localeId: 'tr_TR',
      );
      await Future.delayed(const Duration(seconds: 5));
      await _speech.stop();
      _isListening = false;
      return _recognizedText.isNotEmpty ? _recognizedText : null;
    } catch (e) {
      _isListening = false;
      return null;
    }
  }

  Future<void> stopSpeechRecognition() async {
    if (_isListening) {
      await _speech.stop();
      _isListening = false;
    }
  }
}