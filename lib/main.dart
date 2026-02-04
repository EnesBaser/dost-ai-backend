import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:easy_localization/easy_localization.dart';  // YENİ
import 'screens/chat/chat_screen.dart';
import 'screens/onboarding_screen.dart';
import 'services/storage_service.dart';
import 'services/notification_service.dart';
import 'services/theme_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // EasyLocalization başlat - YENİ
  await EasyLocalization.ensureInitialized();
  
  // Bildirim servisini başlat
  await NotificationService().initialize();
  
  runApp(
    EasyLocalization(  // YENİ - EasyLocalization wrapper
      supportedLocales: const [
        Locale('tr' ),  // Türkçe
        Locale('en' ),  // İngilizce
        Locale('es' ),  // İspanyolca
        Locale('de' ),  // Almanca
		Locale('fr' ),  // Fransızca
      ],
      path: 'assets/translations',  // JSON dosyalarının yolu
      fallbackLocale: const Locale('tr'),  // Varsayılan dil
      startLocale: const Locale('tr' ),  // Başlangıç dili
      child: ChangeNotifierProvider(
        create: (_) => ThemeService(),
        child: const MyApp(),
      ),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    final themeService = Provider.of<ThemeService>(context);
    
    return MaterialApp(
      title: 'Dost AI',
      debugShowCheckedModeBanner: false,
      
      // YENİ - Localization delegates
      localizationsDelegates: context.localizationDelegates,
      supportedLocales: context.supportedLocales,
      locale: context.locale,
      
      theme: themeService.lightTheme,
      darkTheme: themeService.darkTheme,
      themeMode: themeService.isDarkMode ? ThemeMode.dark : ThemeMode.light,
      home: const SplashScreen(),
    );
  }
}

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  final StorageService _storageService = StorageService();

  @override
  void initState() {
    super.initState();
    _checkFirstLaunch();
  }

  Future<void> _checkFirstLaunch() async {
    // Kısa bir splash gösterimi
    await Future.delayed(const Duration(seconds: 1));

    final isFirstLaunch = await _storageService.isFirstLaunch();

    if (mounted) {
      if (isFirstLaunch) {
        // İlk açılış - Onboarding göster
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (context) => const OnboardingScreen()),
        );
      } else {
        // Daha önce kullanılmış - Direkt chat'e git
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (context) => const ChatScreen()),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Color(0xFF667eea),
              Color(0xFF764ba2),
            ],
          ),
        ),
        child: Center(  // YENİ - tr() kullanımı
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text(
                '💬',
                style: TextStyle(fontSize: 80),
              ),
              const SizedBox(height: 20),
              Text(
                'app.name'.tr(),  // YENİ
                style: const TextStyle(
                  fontSize: 36,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                'app.subtitle'.tr(),  // YENİ
                style: const TextStyle(
                  fontSize: 16,
                  color: Colors.white70,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}