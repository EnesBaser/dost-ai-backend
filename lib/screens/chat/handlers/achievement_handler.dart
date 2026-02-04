import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../services/achievements_service.dart';
import '../../../services/chat_history_service.dart';
import '../dialogs/achievement_dialog.dart';

class AchievementHandler {
  final ChatHistoryService chatHistoryService;
  
  AchievementHandler(this.chatHistoryService);
  
  /// Mesaj gönderildikten sonra başarım kontrolü yap
  Future<void> checkMessageAchievement(BuildContext context) async {
    try {
      final achievementsService = AchievementsService();
      final stats = await chatHistoryService.getStatistics();
      final prefs = await SharedPreferences.getInstance();
      
      final totalMessages = stats['user'] ?? 0;
      final streak = prefs.getInt('current_streak') ?? 0;
      final favorites = prefs.getStringList('favorite_messages') ?? [];
      
      final newAchievement = await achievementsService.checkAchievements(
        totalMessages: totalMessages,
        streak: streak,
        favoritesCount: favorites.length,
      );
      
      if (newAchievement != null && context.mounted) {
        AchievementDialog.show(context, newAchievement);
      }
    } catch (e) {
      print('Achievement check error: $e');
    }
  }
  
  /// Ses kullanımı başarımı kontrolü
  Future<void> checkVoiceAchievement(BuildContext context) async {
    try {
      final achievementsService = AchievementsService();
      final prefs = await SharedPreferences.getInstance();
      final hasUsedVoice = prefs.getBool('has_used_voice') ?? false;
      
      if (!hasUsedVoice) {
        await prefs.setBool('has_used_voice', true);
        final achievement = await achievementsService.unlockSpecial('voice_first');
        if (achievement != null && context.mounted) {
          AchievementDialog.show(context, achievement);
        }
      }
    } catch (e) {
      print('Voice achievement error: $e');
    }
  }
}