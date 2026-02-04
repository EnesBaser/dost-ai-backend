import 'package:intl/intl.dart';

class GreetingService {
  static final GreetingService _instance = GreetingService._internal();
  factory GreetingService() => _instance;
  GreetingService._internal();

  // Günün saatine göre selam
  String getTimeBasedGreeting(String? userName) {
    final name = userName ?? 'Arkadaşım';
    final hour = DateTime.now().hour;

    if (hour >= 5 && hour < 12) {
      return 'Günaydın $name! ☀️';
    } else if (hour >= 12 && hour < 17) {
      return 'Merhaba $name! 🌤️';
    } else if (hour >= 17 && hour < 22) {
      return 'İyi akşamlar $name! 🌙';
    } else {
      return 'Gece geç saatler $name! 🌃 Uyuyor musun?';
    }
  }

  // Rastgele check-in mesajları
  List<String> getMorningMessages() {
    return [
      'Günaydın! Bugün planın ne? ☀️',
      'Günaydın! Bugün güzel bir gün olacak! 💫',
      'Sabah sabah! Kahven hazır mı? ☕',
      'Günaydın! Uykun iyi miydi? 😊',
      'Yeni bir gün! Bugün kendine iyi bak! ✨',
    ];
  }

  List<String> getAfternoonMessages() {
    return [
      'Nasıl gidiyor? 🌤️',
      'Öğle arası! Bugün neler yaptın? 🍽️',
      'Günün yarısı geçti! Nasıl geçiyor? ⏰',
      'Merhaba! Öğle yemeği yedin mi? 🥗',
      'Öğleden sonra enerjin nasıl? ⚡',
    ];
  }

  List<String> getEveningMessages() {
    return [
      'Bugün nasıl geçti? 🌙',
      'Akşam oldu! Bugünden memnun musun? ✨',
      'Günün yorucu muydu? 💭',
      'Akşam! Dinlenme zamanı! 🌃',
      'Bugün ne güzel şeyler oldu? 💜',
    ];
  }

  // Rastgele mesaj seç
  String getRandomCheckIn() {
    final hour = DateTime.now().hour;
    List<String> messages;

    if (hour >= 5 && hour < 12) {
      messages = getMorningMessages();
    } else if (hour >= 12 && hour < 17) {
      messages = getAfternoonMessages();
    } else {
      messages = getEveningMessages();
    }

    messages.shuffle();
    return messages.first;
  }

  // Son görülme zamanı kontrolü
  String? getMissYouMessage(DateTime? lastSeen) {
    if (lastSeen == null) return null;

    final daysSince = DateTime.now().difference(lastSeen).inDays;

    if (daysSince >= 3) {
      return 'Seni özledim! 💜 $daysSince gündür konuşmadık!';
    } else if (daysSince >= 1) {
      return 'Merhaba! Nasılsın? Seni görmeyeli $daysSince gün oldu! 😊';
    }

    return null;
  }

  // Hafta sonu mesajı
  String? getWeekendMessage() {
    final weekday = DateTime.now().weekday;
    
    if (weekday == DateTime.saturday) {
      return 'Güzel bir cumartesi! Bugün planın ne? 🎉';
    } else if (weekday == DateTime.sunday) {
      return 'Pazar keyfi! Dinlenebiliyor musun? 🌸';
    }
    
    return null;
  }

  // Özel gün kontrolü (isteğe bağlı)
  String? getSpecialDayMessage(DateTime? birthday) {
    if (birthday == null) return null;

    final today = DateTime.now();
    if (today.month == birthday.month && today.day == birthday.day) {
      return 'DOĞUM GÜNÜN KUTLU OLSUN! 🎂🎉🎈';
    }

    return null;
  }
}