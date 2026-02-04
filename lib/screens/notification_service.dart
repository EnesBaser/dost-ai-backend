import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/timezone.dart' as tz;
import 'package:timezone/data/latest.dart' as tz;

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FlutterLocalNotificationsPlugin _notifications = 
      FlutterLocalNotificationsPlugin();

  bool _isInitialized = false;

  // Bildirim ayarları
  Future<void> initialize() async {
    if (_isInitialized) return;

    // Timezone veritabanını başlat
    tz.initializeTimeZones();
    tz.setLocalLocation(tz.getLocation('Europe/Istanbul'));

    // Android ayarları
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    
    // iOS ayarları
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );

    const initSettings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _notifications.initialize(
      initSettings,
      onDidReceiveNotificationResponse: _onNotificationTapped,
    );

    _isInitialized = true;
  }

  // Bildirime tıklandığında
  void _onNotificationTapped(NotificationResponse response) {
    print('Bildirime tıklandı: ${response.payload}');
    // TODO: Chat ekranını aç
  }

  // İzin iste (Android 13+)
  Future<bool> requestPermission() async {
    final androidPlugin = _notifications
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();
    
    if (androidPlugin != null) {
      final granted = await androidPlugin.requestExactAlarmsPermission();
      return granted ?? false;
    }
    return true;
  }

  // Hemen bildirim gönder
  Future<void> showNotification({
    required int id,
    required String title,
    required String body,
    String? payload,
  }) async {
    const androidDetails = AndroidNotificationDetails(
      'dost_ai_channel',
      'Dost AI Bildirimleri',
      channelDescription: 'Dost AI\'dan gelen mesajlar',
      importance: Importance.high,
      priority: Priority.high,
      icon: '@mipmap/ic_launcher',
    );

    const iosDetails = DarwinNotificationDetails();

    const details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );

    await _notifications.show(id, title, body, details, payload: payload);
  }

  // Zamanlı bildirim (belirli saatte)
  Future<void> scheduleNotification({
    required int id,
    required String title,
    required String body,
    required int hour,
    required int minute,
    String? payload,
  }) async {
    await _notifications.zonedSchedule(
      id,
      title,
      body,
      _nextInstanceOfTime(hour, minute),
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'dost_ai_daily',
          'Günlük Bildirimler',
          channelDescription: 'Sabah ve akşam mesajları',
          importance: Importance.high,
          priority: Priority.high,
          icon: '@mipmap/ic_launcher',
        ),
        iOS: DarwinNotificationDetails(),
      ),
      androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      uiLocalNotificationDateInterpretation:
          UILocalNotificationDateInterpretation.absoluteTime,
      matchDateTimeComponents: DateTimeComponents.time,
      payload: payload,
    );
  }

  // Bir sonraki saat örneğini hesapla
  tz.TZDateTime _nextInstanceOfTime(int hour, int minute) {
    final now = tz.TZDateTime.now(tz.local);
    var scheduledDate = tz.TZDateTime(
      tz.local,
      now.year,
      now.month,
      now.day,
      hour,
      minute,
    );

    // Eğer zaman geçmişse, yarına ayarla
    if (scheduledDate.isBefore(now)) {
      scheduledDate = scheduledDate.add(const Duration(days: 1));
    }

    return scheduledDate;
  }

  // Sabah selamlaşması zamanla
  Future<void> scheduleMorningGreeting(String userName) async {
    await scheduleNotification(
      id: 1,
      title: 'Günaydın $userName! ☀️',
      body: 'Bugün nasılsın? Seninle konuşmayı özledim! 💜',
      hour: 9, // Sabah 9:00
      minute: 0,
      payload: 'morning',
    );
  }

  // Akşam check-in zamanla
  Future<void> scheduleEveningCheckIn(String userName) async {
    await scheduleNotification(
      id: 2,
      title: 'İyi akşamlar $userName! 🌙',
      body: 'Bugün nasıl geçti? Anlatmak ister misin?',
      hour: 20, // Akşam 20:00
      minute: 0,
      payload: 'evening',
    );
  }

  // Öğle hatırlatması
  Future<void> scheduleLunchReminder(String userName) async {
    await scheduleNotification(
      id: 3,
      title: 'Merhaba $userName! 🍽️',
      body: 'Öğle arası! Bugün neler yapıyorsun?',
      hour: 13, // Öğle 13:00
      minute: 0,
      payload: 'lunch',
    );
  }

  // Tüm bildirimleri iptal et
  Future<void> cancelAll() async {
    await _notifications.cancelAll();
  }

  // Belirli bir bildirimi iptal et
  Future<void> cancel(int id) async {
    await _notifications.cancel(id);
  }

  // Bekleyen bildirimleri listele
  Future<List<PendingNotificationRequest>> getPendingNotifications() async {
    return await _notifications.pendingNotificationRequests();
  }
}