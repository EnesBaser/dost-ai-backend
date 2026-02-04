import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import '../../services/achievements_service.dart';

class AchievementsScreen extends StatefulWidget {
  const AchievementsScreen({super.key});

  @override
  State<AchievementsScreen> createState() => _AchievementsScreenState();
}

class _AchievementsScreenState extends State<AchievementsScreen> {
  final AchievementsService achievementsService = AchievementsService();
  List<Achievement> _achievements = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadAchievements();
  }

  Future<void> _loadAchievements() async {
    final achievements = await achievementsService.getAchievements();
    setState(() {
      _achievements = achievements;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(
          backgroundColor: Colors.deepPurple,
          foregroundColor: Colors.white,
          title: Text('achievements.title'.tr()),
        ),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    final unlocked = _achievements.where((a) => a.unlocked).toList();
    final locked = _achievements.where((a) => !a.unlocked).toList();
    final progress = _achievements.isEmpty ? 0.0 : unlocked.length / _achievements.length;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.deepPurple,
        foregroundColor: Colors.white,
        title: Text('achievements.title_emoji'.tr()),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildProgressCard(unlocked.length, _achievements.length, progress),
            const SizedBox(height: 20),

            if (unlocked.isNotEmpty) ...[
              Text('achievements.unlocked'.tr(), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              ...unlocked.map((a) => _buildAchievementCard(a)),
              const SizedBox(height: 20),
            ],

            if (locked.isNotEmpty) ...[
              Text('achievements.locked'.tr(), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              ...locked.map((a) => _buildAchievementCard(a)),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildProgressCard(int unlocked, int total, double progress) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Colors.deepPurple, Colors.purple],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('achievements.progress'.tr(), style: const TextStyle(fontSize: 14, color: Colors.white70)),
              Text(
                'achievements.count'.tr(namedArgs: {'unlocked': unlocked.toString(), 'total': total.toString()}),
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)
              ),
            ],
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 12,
              backgroundColor: Colors.white24,
              valueColor: const AlwaysStoppedAnimation<Color>(Colors.amber),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'achievements.completed'.tr(namedArgs: {'percent': (progress * 100).toStringAsFixed(0)}),
            style: const TextStyle(fontSize: 13, color: Colors.white70),
          ),
        ],
      ),
    );
  }

  Widget _buildAchievementCard(Achievement achievement) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: achievement.unlocked
            ? (isDark ? const Color(0xFF2A2A2A) : Colors.white)
            : (isDark ? const Color(0xFF1E1E1E) : Colors.grey[100]),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: achievement.unlocked ? Colors.amber.withOpacity(0.5) : Colors.grey.withOpacity(0.2),
        ),
        boxShadow: achievement.unlocked
            ? [BoxShadow(color: Colors.amber.withOpacity(0.15), blurRadius: 8, offset: const Offset(0, 2))]
            : [],
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: achievement.unlocked
                  ? Colors.amber.withOpacity(0.15)
                  : Colors.grey.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(
                achievement.unlocked ? achievement.emoji : '🔒',
                style: const TextStyle(fontSize: 24),
              ),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  achievement.title,
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: achievement.unlocked ? null : Colors.grey,
                  ),
                ),
                Text(
                  achievement.description,
                  style: TextStyle(
                    fontSize: 12,
                    color: achievement.unlocked ? Colors.grey : Colors.grey[500],
                  ),
                ),
              ],
            ),
          ),
          if (achievement.unlocked)
            const Icon(Icons.check_circle, color: Colors.amber, size: 22),
        ],
      ),
    );
  }
}