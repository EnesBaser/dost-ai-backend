import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class ChatHistoryService {
  static final ChatHistoryService _instance = ChatHistoryService._internal();
  factory ChatHistoryService() => _instance;
  ChatHistoryService._internal();

  static const String _historyKey = 'chat_history';
  static const int _maxHistorySize = 500; // Son 500 mesaj

  // Mesajı kaydet
  Future<void> saveMessage({
    required String role,
    required String message,
    required DateTime timestamp,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final history = await getAllMessages();

    history.add({
      'role': role,
      'message': message,
      'timestamp': timestamp.toIso8601String(),
    });

    // Maksimum boyutu aşarsa eski mesajları sil
    if (history.length > _maxHistorySize) {
      history.removeRange(0, history.length - _maxHistorySize);
    }

    await prefs.setString(_historyKey, jsonEncode(history));
  }

  // Tüm mesajları getir
  Future<List<Map<String, dynamic>>> getAllMessages() async {
    final prefs = await SharedPreferences.getInstance();
    final historyString = prefs.getString(_historyKey);

    if (historyString != null) {
      final List<dynamic> decoded = jsonDecode(historyString);
      return decoded.map((e) => Map<String, dynamic>.from(e)).toList();
    }

    return [];
  }

  // Mesajları ara
  Future<List<Map<String, dynamic>>> searchMessages(String query) async {
    final allMessages = await getAllMessages();
    final lowerQuery = query.toLowerCase();

    return allMessages.where((msg) {
      final message = msg['message'] as String;
      return message.toLowerCase().contains(lowerQuery);
    }).toList();
  }

  // Son N mesajı getir
  Future<List<Map<String, dynamic>>> getRecentMessages(int count) async {
    final allMessages = await getAllMessages();
    
    if (allMessages.length <= count) {
      return allMessages;
    }

    return allMessages.sublist(allMessages.length - count);
  }

  // Tarihe göre mesajları getir
  Future<List<Map<String, dynamic>>> getMessagesByDate(DateTime date) async {
    final allMessages = await getAllMessages();

    return allMessages.where((msg) {
      final timestamp = DateTime.parse(msg['timestamp'] as String);
      return timestamp.year == date.year &&
          timestamp.month == date.month &&
          timestamp.day == date.day;
    }).toList();
  }

  // Bugünkü mesajlar (Turkey timezone ile tutarlı)
  Future<List<Map<String, dynamic>>> getTodayMessages() async {
    final allMessages = await getAllMessages();
    final now = DateTime.now().toUtc().add(const Duration(hours: 3));

    return allMessages.where((msg) {
      final timestamp = DateTime.parse(msg['timestamp'] as String);
      // Eğer UTC olarak kaydedildiyse Turkey'ye çevir
      final turkeyTime = timestamp.isUtc
          ? timestamp.add(const Duration(hours: 3))
          : timestamp;

      return turkeyTime.year == now.year &&
          turkeyTime.month == now.month &&
          turkeyTime.day == now.day;
    }).toList();
  }

  // Bu haftaki mesajlar
  Future<List<Map<String, dynamic>>> getThisWeekMessages() async {
    final allMessages = await getAllMessages();
    final now = DateTime.now();
    final weekAgo = now.subtract(const Duration(days: 7));

    return allMessages.where((msg) {
      final timestamp = DateTime.parse(msg['timestamp'] as String);
      return timestamp.isAfter(weekAgo);
    }).toList();
  }

  // İstatistikler
  Future<Map<String, int>> getStatistics() async {
    final allMessages = await getAllMessages();
    
    int userMessages = 0;
    int aiMessages = 0;
    
    for (var msg in allMessages) {
      if (msg['role'] == 'user') {
        userMessages++;
      } else {
        aiMessages++;
      }
    }

    return {
      'total': allMessages.length,
      'user': userMessages,
      'ai': aiMessages,
    };
  }

  // Tüm geçmişi temizle
  Future<void> clearHistory() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_historyKey);
  }

  // Belirli bir mesajı sil
  Future<void> deleteMessage(int index) async {
    final prefs = await SharedPreferences.getInstance();
    final history = await getAllMessages();

    if (index >= 0 && index < history.length) {
      history.removeAt(index);
      await prefs.setString(_historyKey, jsonEncode(history));
    }
  }
}