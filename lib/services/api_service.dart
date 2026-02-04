import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  // Geliştirme/Üretim modu
  static const bool isDevelopment = true;
  
  // Development: Localhost
  static const String devUrl = 'http://10.0.2.2:5001';
  
  // Production: Gerçek sunucu (daha sonra eklenecek)
  static const String prodUrl = 'https://your-production-url.com';
  
  // Aktif URL
  static String get baseUrl => isDevelopment ? devUrl : prodUrl;
  
  // Health check
  Future<bool> checkHealth() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/health'),
        headers: {
          'Content-Type': 'application/json; charset=UTF-8',
        },
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        return data['status'] == 'ok';
      }
      return false;
    } catch (e) {
      print('Health check hatası: $e');
      return false;
    }
  }
  
  // Chat mesajı gönder
  Future<String> sendMessage(
    String message, {
    String? userName,
    List<String>? interests,
    String? emotion,
  }) async {
    try {
      final requestBody = {
        'message': message,
        if (userName != null) 'user_name': userName,
        if (interests != null && interests.isNotEmpty) 'interests': interests,
        if (emotion != null) 'emotion': emotion,
      };
      
      final response = await http.post(
        Uri.parse('$baseUrl/chat'),
        headers: {
          'Content-Type': 'application/json; charset=UTF-8',
        },
        body: jsonEncode(requestBody),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        return data['response'] ?? 'Yanıt alınamadı';
      } else {
        return 'Hata: ${response.statusCode}';
      }
    } catch (e) {
      return 'Bağlantı hatası: $e';
    }
  }
}