import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:easy_localization/easy_localization.dart';
import '../services/notification_service.dart';
import '../services/storage_service.dart';
import '../services/theme_service.dart';
import '../models/user_profile.dart';

class NotificationSettingsScreen extends StatefulWidget {
  const NotificationSettingsScreen({super.key});

  @override
  State<NotificationSettingsScreen> createState() =>
      _NotificationSettingsScreenState();
}

class _NotificationSettingsScreenState
    extends State<NotificationSettingsScreen> {
  final NotificationService _notificationService = NotificationService();
  final StorageService _storageService = StorageService();
  
  bool _morningEnabled = false;
  bool _lunchEnabled = false;
  bool _eveningEnabled = false;
  UserProfile? _userProfile;
  
  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    _userProfile = await _storageService.getUserProfile();
    
    // Bildirim izni kontrol et
    await _notificationService.initialize();
    
    setState(() {});
  }

  Future<void> _toggleMorning(bool value) async {
    if (value) {
      final permission = await _notificationService.requestPermission();
      if (!permission) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('notifications.permission_required'.tr()),
            ),
          );
        }
        return;
      }
      
      await _notificationService.scheduleMorningGreeting(
        _userProfile?.displayName ?? 'notifications.morning_greeting'.tr(namedArgs: {'name': 'Arkadaşım'}),
      );
    } else {
      await _notificationService.cancel(1);
    }
    
    setState(() {
      _morningEnabled = value;
    });
  }

  Future<void> _toggleLunch(bool value) async {
    if (value) {
      final permission = await _notificationService.requestPermission();
      if (!permission) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('notifications.permission_required'.tr()),
            ),
          );
        }
        return;
      }
      
      await _notificationService.scheduleLunchReminder(
        _userProfile?.displayName ?? 'Arkadaşım',
      );
    } else {
      await _notificationService.cancel(3);
    }
    
    setState(() {
      _lunchEnabled = value;
    });
  }

  Future<void> _toggleEvening(bool value) async {
    if (value) {
      final permission = await _notificationService.requestPermission();
      if (!permission) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('notifications.permission_required'.tr()),
            ),
          );
        }
        return;
      }
      
      await _notificationService.scheduleEveningCheckIn(
        _userProfile?.displayName ?? 'Arkadaşım',
      );
    } else {
      await _notificationService.cancel(2);
    }
    
    setState(() {
      _eveningEnabled = value;
    });
  }

  Future<void> _testNotification() async {
    await _notificationService.showNotification(
      id: 999,
      title: 'notifications.test_title'.tr(),
      body: 'notifications.test_body'.tr(),
    );
  }

  // YENİ - Dil değiştirme
  void _changeLanguage(String languageCode) async {
    await context.setLocale(Locale(languageCode));
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('notifications.title'.tr()),
        backgroundColor: Colors.deepPurple,
        foregroundColor: Colors.white,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // YENİ - Dil Seçici Bölümü
          Text(
            '🌍 ${'Language / Dil'}',
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            'Select your preferred language / Tercih ettiğiniz dili seçin',
            style: const TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 20),
          Card(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: DropdownButton<String>(
                isExpanded: true,
                value: context.locale.languageCode,
                underline: const SizedBox(),
                items: const [
                  DropdownMenuItem(value: 'tr', child: Text('🇹🇷 Türkçe')),
                  DropdownMenuItem(value: 'en', child: Text('🇬🇧 English')),
                  DropdownMenuItem(value: 'es', child: Text('🇪🇸 Español')),
                  DropdownMenuItem(value: 'de', child: Text('🇩🇪 Deutsch')),
                  DropdownMenuItem(value: 'fr', child: Text('🇫🇷 Français')),
                ],
                onChanged: (value) {
                  if (value != null) {
                    _changeLanguage(value);
                  }
                },
              ),
            ),
          ),
          const SizedBox(height: 30),

          Text(
            'notifications.daily_reminders'.tr(),
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            'notifications.daily_subtitle'.tr(),
            style: const TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 20),

          // Sabah bildirimi
          Card(
            child: SwitchListTile(
              title: Text('notifications.morning'.tr()),
              subtitle: Text('notifications.morning_subtitle'.tr()),
              value: _morningEnabled,
              onChanged: _toggleMorning,
              secondary: const Icon(Icons.wb_sunny, color: Colors.orange),
            ),
          ),
          const SizedBox(height: 10),

          // Öğle bildirimi
          Card(
            child: SwitchListTile(
              title: Text('notifications.lunch'.tr()),
              subtitle: Text('notifications.lunch_subtitle'.tr()),
              value: _lunchEnabled,
              onChanged: _toggleLunch,
              secondary: const Icon(Icons.lunch_dining, color: Colors.green),
            ),
          ),
          const SizedBox(height: 10),

          // Akşam bildirimi
          Card(
            child: SwitchListTile(
              title: Text('notifications.evening'.tr()),
              subtitle: Text('notifications.evening_subtitle'.tr()),
              value: _eveningEnabled,
              onChanged: _toggleEvening,
              secondary: const Icon(Icons.nightlight, color: Colors.indigo),
            ),
          ),
          const SizedBox(height: 30),

          // Görünüm ayarları bölümü
          Text(
            'notifications.appearance'.tr(),
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            'notifications.appearance_subtitle'.tr(),
            style: const TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 20),

          // Karanlık mod
          Card(
            child: Consumer<ThemeService>(
              builder: (context, themeService, child) {
                return SwitchListTile(
                  title: Text('notifications.dark_mode'.tr()),
                  subtitle: Text(
                    themeService.isDarkMode 
                        ? 'notifications.dark_mode_active'.tr()
                        : 'notifications.light_mode_active'.tr()
                  ),
                  value: themeService.isDarkMode,
                  onChanged: (value) {
                    themeService.toggleTheme();
                  },
                  secondary: Icon(
                    themeService.isDarkMode ? Icons.dark_mode : Icons.light_mode,
                    color: themeService.isDarkMode ? Colors.indigo : Colors.orange,
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 30),

          // Test butonu
          ElevatedButton.icon(
            onPressed: _testNotification,
            icon: const Icon(Icons.notifications_active),
            label: Text('notifications.test_notification'.tr()),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.deepPurple,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.all(15),
            ),
          ),
          const SizedBox(height: 20),

          // Bilgi kutusu
          Container(
            padding: const EdgeInsets.all(15),
            decoration: BoxDecoration(
              color: Colors.blue.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: Colors.blue.withOpacity(0.3)),
            ),
            child: Row(
              children: [
                const Icon(Icons.info_outline, color: Colors.blue),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'notifications.info'.tr(),
                    style: const TextStyle(fontSize: 13),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}