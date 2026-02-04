import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart' hide tr;
import '../../../models/user_profile.dart';
import '../../search_screen.dart';
import '../../profile_screen.dart';
import '../../mood_graph_screen.dart';
import '../../achievements_screen.dart';
import '../../../services/pdf_export_service.dart';
import 'dost_avatar.dart';

class ChatAppBar extends StatelessWidget implements PreferredSizeWidget {
  final UserProfile? userProfile;
  final bool isBackendHealthy;
  final bool wakeWordEnabled;
  final bool ttsEnabled;
  final int currentStreak;
  final AvatarEmotion currentEmotion; 
  final int favoritesCount;
  final List<Map<String, dynamic>> messages;
  final VoidCallback onWakeWordToggle;
  final VoidCallback onTTSToggle;
  final VoidCallback onRefresh;
  final VoidCallback onFavoritesPress;

  const ChatAppBar({
    super.key,
    required this.userProfile,
    required this.isBackendHealthy,
    required this.wakeWordEnabled,
    required this.ttsEnabled,
    required this.currentStreak,
	required this.currentEmotion,
    required this.favoritesCount,
    required this.messages,
    required this.onWakeWordToggle,
    required this.onTTSToggle,
    required this.onRefresh,
    required this.onFavoritesPress,
  });

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);

  @override
  Widget build(BuildContext context) {
    return AppBar(
      backgroundColor: Colors.deepPurple,
      foregroundColor: Colors.white,
      title: Row(
  children: [
    // Avatar (küçük)
    DostAvatar(
      emotion: currentEmotion,
      size: 36, // Küçük boyut
    ),
    const SizedBox(width: 12),
    Expanded(
      child: Text(
        userProfile != null 
            ? 'chat.title'.tr(namedArgs: {'name': userProfile!.displayName})
            : 'app.name'.tr(),
      ),
    ),
    
    // ... streak ve health indicator devam eder
          if (currentStreak > 0) ...[
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.orange,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('🔥', style: TextStyle(fontSize: 14)),
                  const SizedBox(width: 4),
                  Text(
                    '$currentStreak',
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
          ],
          Container(
            width: 10,
            height: 10,
            decoration: BoxDecoration(
              color: isBackendHealthy ? Colors.green : Colors.red,
              shape: BoxShape.circle,
            ),
          ),
        ],
      ),
      actions: [
        IconButton(
          icon: Icon(
            wakeWordEnabled ? Icons.hearing : Icons.hearing_disabled,
            color: wakeWordEnabled ? Colors.green : Colors.white,
          ),
          onPressed: onWakeWordToggle,
          tooltip: wakeWordEnabled ? 'chat.wake_word_active'.tr() : 'chat.wake_word_inactive'.tr(),
        ),
        IconButton(
          icon: Icon(
            ttsEnabled ? Icons.volume_up : Icons.volume_off,
            color: ttsEnabled ? Colors.green : Colors.white,
          ),
          onPressed: onTTSToggle,
          tooltip: ttsEnabled ? 'chat.tts_active'.tr() : 'chat.tts_inactive'.tr(),
        ),
        Stack(
          alignment: Alignment.topRight,
          children: [
            IconButton(
              icon: const Icon(Icons.star_outline),
              onPressed: onFavoritesPress,
              tooltip: 'menu.favorites'.tr(),
            ),
            if (favoritesCount > 0)
              Positioned(
                top: 4,
                right: 4,
                child: Container(
                  padding: const EdgeInsets.all(3),
                  decoration: BoxDecoration(
                    color: Colors.amber,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    '$favoritesCount',
                    style: const TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: Colors.black,
                    ),
                  ),
                ),
              ),
          ],
        ),
        IconButton(
          icon: const Icon(Icons.search),
          onPressed: () {
            Navigator.of(context).push(
              MaterialPageRoute(builder: (context) => const SearchScreen()),
            );
          },
        ),
        IconButton(
          icon: const Icon(Icons.person),
          onPressed: () {
            Navigator.of(context).push(
              MaterialPageRoute(builder: (context) => const ProfileScreen()),
            );
          },
        ),
        IconButton(
          icon: const Icon(Icons.emoji_events),
          onPressed: () {
            Navigator.of(context).push(
              MaterialPageRoute(builder: (context) => const AchievementsScreen()),
            );
          },
          tooltip: 'menu.achievements'.tr(),
        ),
        IconButton(
          icon: const Icon(Icons.bar_chart),
          onPressed: () {
            Navigator.of(context).push(
              MaterialPageRoute(builder: (context) => const MoodGraphScreen()),
            );
          },
          tooltip: 'menu.mood_graph'.tr(),
        ),
        IconButton(
          icon: const Icon(Icons.refresh),
          onPressed: onRefresh,
        ),
        PopupMenuButton<String>(
          icon: const Icon(Icons.more_vert),
          onSelected: (value) async {
            if (messages.isEmpty) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('menu.no_messages'.tr())),
              );
              return;
            }

            final pdfService = PDFExportService();
            final userName = userProfile?.displayName ?? 'menu.stat_user'.tr();
            
            List<Map<String, dynamic>> filteredMessages = messages;
            
            if (value == 'export_7') {
              final sevenDaysAgo = DateTime.now().subtract(const Duration(days: 7));
              filteredMessages = messages.where((msg) {
                final timestamp = msg['timestamp'] as DateTime;
                return timestamp.isAfter(sevenDaysAgo);
              }).toList();
            } else if (value == 'export_30') {
              final thirtyDaysAgo = DateTime.now().subtract(const Duration(days: 30));
              filteredMessages = messages.where((msg) {
                final timestamp = msg['timestamp'] as DateTime;
                return timestamp.isAfter(thirtyDaysAgo);
              }).toList();
            }

            if (filteredMessages.isEmpty) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('menu.no_messages_range'.tr())),
              );
              return;
            }

            final file = await pdfService.exportChatHistory(
              messages: filteredMessages,
              userName: userName,
            );

            if (file != null && context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('menu.pdf_saved'.tr(namedArgs: {'path': file.path}))),
              );
            }
          },
          itemBuilder: (context) => [
            PopupMenuItem<String>(
              value: 'export_all',
              child: Row(
                children: [
                  const Icon(Icons.picture_as_pdf, color: Colors.red),
                  const SizedBox(width: 10),
                  Text('menu.export_all'.tr()),
                ],
              ),
            ),
            PopupMenuItem<String>(
              value: 'export_7',
              child: Row(
                children: [
                  const Icon(Icons.calendar_view_week, color: Colors.deepPurple),
                  const SizedBox(width: 10),
                  Text('menu.export_7_days'.tr()),
                ],
              ),
            ),
            PopupMenuItem<String>(
              value: 'export_30',
              child: Row(
                children: [
                  const Icon(Icons.calendar_month, color: Colors.blue),
                  const SizedBox(width: 10),
                  Text('menu.export_30_days'.tr()),
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }
}