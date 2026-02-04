import 'package:shared_preferences/shared_preferences.dart';
import 'package:easy_localization/easy_localization.dart';
import 'dart:convert';

class Achievement {
  final String id;
  final String title;
  final String emoji;
  final String description;
  final bool unlocked;
  final DateTime? unlockedAt;

  Achievement({
    required this.id,
    required this.title,
    required this.emoji,
    required this.description,
    this.unlocked = false,
    this.unlockedAt,
  });

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'emoji': emoji,
    'description': description,
    'unlocked': unlocked,
    'unlockedAt': unlockedAt?.toIso8601String(),
  };

  factory Achievement.fromJson(Map<String, dynamic> json) => Achievement(
    id: json['id'],
    title: json['title'],
    emoji: json['emoji'],
    description: json['description'],
    unlocked: json['unlocked'] ?? false,
    unlockedAt: json['unlockedAt'] != null ? DateTime.parse(json['unlockedAt']) : null,
  );
}

class AchievementsService {
  static final AchievementsService _instance = AchievementsService._internal();
  factory AchievementsService() => _instance;
  AchievementsService._internal();

  static const String _key = 'achievements';

  // Tüm olası başarımlar - dinamik olarak oluştur (çeviri için)
  static List<Achievement> _getAllAchievements() {
    return [
      // Mesaj başarımları
      Achievement(
        id: 'msg_10',
        title: 'achievements.msg_10.title'.tr(),
        emoji: '🌱',
        description: 'achievements.msg_10.description'.tr(),
      ),
      Achievement(
        id: 'msg_50',
        title: 'achievements.msg_50.title'.tr(),
        emoji: '💬',
        description: 'achievements.msg_50.description'.tr(),
      ),
      Achievement(
        id: 'msg_100',
        title: 'achievements.msg_100.title'.tr(),
        emoji: '🗣️',
        description: 'achievements.msg_100.description'.tr(),
      ),
      Achievement(
        id: 'msg_500',
        title: 'achievements.msg_500.title'.tr(),
        emoji: '🏅',
        description: 'achievements.msg_500.description'.tr(),
      ),

      // Streak başarımları
      Achievement(
        id: 'streak_3',
        title: 'achievements.streak_3.title'.tr(),
        emoji: '🔥',
        description: 'achievements.streak_3.description'.tr(),
      ),
      Achievement(
        id: 'streak_7',
        title: 'achievements.streak_7.title'.tr(),
        emoji: '⚔️',
        description: 'achievements.streak_7.description'.tr(),
      ),
      Achievement(
        id: 'streak_14',
        title: 'achievements.streak_14.title'.tr(),
        emoji: '💪',
        description: 'achievements.streak_14.description'.tr(),
      ),
      Achievement(
        id: 'streak_30',
        title: 'achievements.streak_30.title'.tr(),
        emoji: '🦸',
        description: 'achievements.streak_30.description'.tr(),
      ),

      // Favori başarımları
      Achievement(
        id: 'fav_1',
        title: 'achievements.fav_1.title'.tr(),
        emoji: '⭐',
        description: 'achievements.fav_1.description'.tr(),
      ),
      Achievement(
        id: 'fav_10',
        title: 'achievements.fav_10.title'.tr(),
        emoji: '🌟',
        description: 'achievements.fav_10.description'.tr(),
      ),

      // Özel başarımlar
      Achievement(
        id: 'voice_first',
        title: 'achievements.voice_first.title'.tr(),
        emoji: '🎤',
        description: 'achievements.voice_first.description'.tr(),
      ),
      Achievement(
        id: 'search_first',
        title: 'achievements.search_first.title'.tr(),
        emoji: '🔍',
        description: 'achievements.search_first.description'.tr(),
      ),
    ];
  }

  // Kaydedilen başarımları yükle
  Future<List<Achievement>> getAchievements() async {
    final allAchievements = _getAllAchievements();
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_key);

    if (saved == null) return allAchievements;

    final savedList = jsonDecode(saved) as List;
    final savedMap = {for (var item in savedList) item['id']: item};

    return allAchievements.map((a) {
      if (savedMap.containsKey(a.id)) {
        final s = savedMap[a.id]!;
        return Achievement(
          id: a.id,
          title: a.title,
          emoji: a.emoji,
          description: a.description,
          unlocked: s['unlocked'] ?? false,
          unlockedAt: s['unlockedAt'] != null ? DateTime.parse(s['unlockedAt']) : null,
        );
      }
      return a;
    }).toList();
  }

  // Başarım kilit açma kontrolü – yeni açılan başarımı döndürür (null = yeni yok)
  Future<Achievement?> checkAchievements({
    required int totalMessages,
    required int streak,
    required int favoritesCount,
  }) async {
    final achievements = await getAchievements();
    Achievement? newlyUnlocked;

    for (var a in achievements) {
      if (a.unlocked) continue;

      bool shouldUnlock = false;

      switch (a.id) {
        case 'msg_10': shouldUnlock = totalMessages >= 10; break;
        case 'msg_50': shouldUnlock = totalMessages >= 50; break;
        case 'msg_100': shouldUnlock = totalMessages >= 100; break;
        case 'msg_500': shouldUnlock = totalMessages >= 500; break;
        case 'streak_3': shouldUnlock = streak >= 3; break;
        case 'streak_7': shouldUnlock = streak >= 7; break;
        case 'streak_14': shouldUnlock = streak >= 14; break;
        case 'streak_30': shouldUnlock = streak >= 30; break;
        case 'fav_1': shouldUnlock = favoritesCount >= 1; break;
        case 'fav_10': shouldUnlock = favoritesCount >= 10; break;
      }

      if (shouldUnlock) {
        newlyUnlocked = Achievement(
          id: a.id,
          title: a.title,
          emoji: a.emoji,
          description: a.description,
          unlocked: true,
          unlockedAt: DateTime.now(),
        );
        break; // Bir seferinde sadece 1 tane göster
      }
    }

    if (newlyUnlocked != null) {
      await _saveUnlocked(newlyUnlocked);
    }

    return newlyUnlocked;
  }

  // Özel başarımları Manuel tetikle (ses, arama vs.)
  Future<Achievement?> unlockSpecial(String id) async {
    final achievements = await getAchievements();
    final achievement = achievements.firstWhere(
      (a) => a.id == id,
      orElse: () => Achievement(id: '', title: '', emoji: '', description: ''),
    );

    if (achievement.id.isEmpty || achievement.unlocked) return null;

    final unlocked = Achievement(
      id: achievement.id,
      title: achievement.title,
      emoji: achievement.emoji,
      description: achievement.description,
      unlocked: true,
      unlockedAt: DateTime.now(),
    );

    await _saveUnlocked(unlocked);
    return unlocked;
  }

  Future<void> _saveUnlocked(Achievement achievement) async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_key);
    List<Map<String, dynamic>> list = saved != null ? List<Map<String, dynamic>>.from(jsonDecode(saved)) : [];

    list.removeWhere((item) => item['id'] == achievement.id);
    list.add(achievement.toJson());

    await prefs.setString(_key, jsonEncode(list));
  }

  // İstatistikler
  Future<Map<String, int>> getStats() async {
    final achievements = await getAchievements();
    return {
      'total': achievements.length,
      'unlocked': achievements.where((a) => a.unlocked).length,
    };
  }
}