import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/storage_service.dart';
import '../services/theme_service.dart';
import '../models/user_profile.dart';
import 'notification_settings_screen.dart';
import 'onboarding_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final StorageService _storageService = StorageService();
  UserProfile? _userProfile;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    final profile = await _storageService.getUserProfile();
    setState(() {
      _userProfile = profile;
      _isLoading = false;
    });
  }

  Future<void> _resetOnboarding() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('profile.reset_confirm_title'.tr()),
        content: Text('profile.reset_confirm_message'.tr()),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text('common.cancel'.tr()),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: Text('profile.reset_profile'.tr()),
          ),
        ],
      ),
    );

    if (confirm == true && mounted) {
      await _storageService.clearUserProfile();
      
      // Tüm cache'i temizle
      final prefs = await SharedPreferences.getInstance();
      await prefs.clear();
      
      if (mounted) {
        // Tüm stack'i temizle ve onboarding'e git
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (context) => const OnboardingScreen()),
          (route) => false,
        );
      }
    }
  }

  String _formatDate(DateTime date) {
    final months = [
      'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
      'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'
    ];
    return '${date.day} ${months[date.month - 1]} ${date.year}';
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(
          title: Text('profile.title'.tr()),
          backgroundColor: Colors.deepPurple,
          foregroundColor: Colors.white,
        ),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_userProfile == null) {
      // Profil yoksa onboarding'e yönlendir
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          Navigator.of(context).pushAndRemoveUntil(
            MaterialPageRoute(builder: (context) => const OnboardingScreen()),
            (route) => false,
          );
        }
      });
      
      return Scaffold(
        appBar: AppBar(
          title: Text('profile.title'.tr()),
          backgroundColor: Colors.deepPurple,
          foregroundColor: Colors.white,
        ),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text('profile.title'.tr()),
        backgroundColor: Colors.deepPurple,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            _buildProfileHeader(),
            _buildInterestsSection(),
            _buildStatsSection(),
            _buildSettingsSection(),
          ],
        ),
      ),
    );
  }

  Widget _buildProfileHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(30),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.deepPurple, Colors.purple],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: Column(
        children: [
          const CircleAvatar(
            radius: 50,
            backgroundColor: Colors.white,
            child: Icon(Icons.person, size: 60, color: Colors.deepPurple),
          ),
          const SizedBox(height: 16),
          Text(
            _userProfile!.name,
            style: const TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          if (_userProfile!.displayName != _userProfile!.name) ...[
            const SizedBox(height: 4),
            Text(
              '"${_userProfile!.displayName}"',
              style: const TextStyle(
                fontSize: 16,
                color: Colors.white70,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
          const SizedBox(height: 8),
          Text(
            'profile.membership'.tr(namedArgs: {'date': _formatDate(_userProfile!.createdAt)}),
            style: const TextStyle(
              fontSize: 14,
              color: Colors.white70,
            ),
          ),
        ],
      ),
    );
  }
Widget _buildInterestsSection() {
  if (_userProfile!.interests == null || _userProfile!.interests!.isEmpty) {
    return const SizedBox.shrink();
  }

  return Padding(
    padding: const EdgeInsets.all(20),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'profile.my_interests'.tr(),
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: _userProfile!.interests!.map((interest) {
            // İlgi alanını çevir
            final translatedInterest = _translateInterest(interest);
            return Chip(
              label: Text(translatedInterest),
              backgroundColor: Colors.deepPurple.withOpacity(0.1),
              labelStyle: const TextStyle(color: Colors.deepPurple),
            );
          }).toList(),
        ),
      ],
    ),
  );
}

// Yeni fonksiyon ekle
String _translateInterest(String interest) {
  final interestKey = interest.toLowerCase().replaceAll('ö', 'o').replaceAll('ü', 'u').replaceAll('ş', 's').replaceAll('ç', 'c').replaceAll('ğ', 'g').replaceAll('ı', 'i');
  
  switch (interestKey) {
    case 'teknoloji': return 'onboarding.interests.tech'.tr();
    case 'spor': return 'onboarding.interests.sports'.tr();
    case 'muzik': return 'onboarding.interests.music'.tr();
    case 'müzik': return 'onboarding.interests.music'.tr();
    case 'film/dizi': return 'onboarding.interests.movies'.tr();
    case 'kitap': return 'onboarding.interests.books'.tr();
    case 'seyahat': return 'onboarding.interests.travel'.tr();
    case 'yemek': return 'onboarding.interests.food'.tr();
    case 'sanat': return 'onboarding.interests.art'.tr();
    case 'oyun': return 'onboarding.interests.games'.tr();
    case 'bilim': return 'onboarding.interests.science'.tr();
    default: return interest; // Bilinmeyen ilgi alanı ise olduğu gibi döndür
  }
}

  Widget _buildStatsSection() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'profile.statistics'.tr(),
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          _buildStatCard(
            title: 'profile.total_messages'.tr(),
            value: '0',
            icon: Icons.chat_bubble,
            color: Colors.blue,
          ),
          const SizedBox(height: 10),
          _buildStatCard(
            title: 'profile.active_days'.tr(),
            value: 'profile.days_count'.tr(namedArgs: {
              'count': DateTime.now().difference(_userProfile!.createdAt).inDays.toString()
            }),
            icon: Icons.calendar_today,
            color: Colors.green,
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: color.withOpacity(0.2),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 14,
                    color: Colors.grey,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  value,
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSettingsSection() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'profile.settings'.tr(),
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          _buildSettingsTile(
            icon: Icons.edit,
            title: 'profile.edit_profile'.tr(),
            subtitle: 'profile.edit_profile_subtitle'.tr(),
            color: Colors.deepPurple,
            onTap: () {
              showDialog(
                context: context,
                builder: (context) => AlertDialog(
                  content: Text('profile.coming_soon'.tr()),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: Text('common.ok'.tr()),
                    ),
                  ],
                ),
              );
            },
          ),
          const SizedBox(height: 10),
          _buildSettingsTile(
            icon: Icons.notifications,
            title: 'profile.notifications'.tr(),
            subtitle: 'profile.notifications_subtitle'.tr(),
            color: Colors.orange,
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => const NotificationSettingsScreen(),
                ),
              );
            },
          ),
          const SizedBox(height: 10),
          _buildSettingsTile(
            icon: Icons.refresh,
            title: 'profile.reset_profile'.tr(),
            subtitle: 'profile.reset_profile_subtitle'.tr(),
            color: Colors.red,
            onTap: _resetOnboarding,
          ),
        ],
      ),
    );
  }

  Widget _buildSettingsTile({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          border: Border.all(color: Colors.grey.withOpacity(0.2)),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: color, size: 24),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: const TextStyle(
                      fontSize: 13,
                      color: Colors.grey,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: Colors.grey),
          ],
        ),
      ),
    );
  }
}