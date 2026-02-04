import 'package:shared_preferences/shared_preferences.dart';

class StreakService {
  static const String _lastVisitKey = 'last_visit_date';
  static const String _streakCountKey = 'streak_count';

  /// Streak'i güncelle ve döndür
  Future<int> updateStreak() async {
    final prefs = await SharedPreferences.getInstance();
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    
    final lastVisitString = prefs.getString(_lastVisitKey);
    final currentStreak = prefs.getInt(_streakCountKey) ?? 0;
    
    if (lastVisitString == null) {
      // İlk ziyaret
      await prefs.setString(_lastVisitKey, today.toIso8601String());
      await prefs.setInt(_streakCountKey, 1);
      return 1;
    }
    
    final lastVisit = DateTime.parse(lastVisitString);
    final lastVisitDay = DateTime(lastVisit.year, lastVisit.month, lastVisit.day);
    final daysDifference = today.difference(lastVisitDay).inDays;
    
    if (daysDifference == 0) {
      // Bugün zaten giriş yapmış
      return currentStreak;
    } else if (daysDifference == 1) {
      // Ardışık gün - streak devam ediyor
      final newStreak = currentStreak + 1;
      await prefs.setString(_lastVisitKey, today.toIso8601String());
      await prefs.setInt(_streakCountKey, newStreak);
      return newStreak;
    } else {
      // Streak kırıldı - yeniden başla
      await prefs.setString(_lastVisitKey, today.toIso8601String());
      await prefs.setInt(_streakCountKey, 1);
      return 1;
    }
  }

  /// Mevcut streak'i al
  Future<int> getStreak() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(_streakCountKey) ?? 0;
  }

  /// Streak mesajı oluştur
  String getStreakMessage(int streak) {
    if (streak == 1) {
      return '🔥 1 gün';
    } else if (streak == 7) {
      return '🔥 7 gün - Muhteşemsin! 🎉';
    } else if (streak == 30) {
      return '🔥 30 gün - İnanılmaz! 🏆';
    } else if (streak >= 100) {
      return '🔥 $streak gün - Efsanesin! 👑';
    } else if (streak >= 50) {
      return '🔥 $streak gün - Harikasın! ⭐';
    } else if (streak >= 14) {
      return '🔥 $streak gün - Süpersin! 💪';
    } else {
      return '🔥 $streak gün';
    }
  }
}
