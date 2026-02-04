import 'package:shared_preferences/shared_preferences.dart';

class SpecialDaysService {
  static final SpecialDaysService _instance = SpecialDaysService._internal();
  factory SpecialDaysService() => _instance;
  SpecialDaysService._internal();

  // Doğum günü kaydet
  Future<void> saveBirthday(DateTime birthday) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('birthday', birthday.toIso8601String());
  }

  // Doğum günü getir
  Future<DateTime?> getBirthday() async {
    final prefs = await SharedPreferences.getInstance();
    final birthdayString = prefs.getString('birthday');
    
    if (birthdayString != null) {
      return DateTime.parse(birthdayString);
    }
    return null;
  }

  // Bugün doğum günü mü?
  Future<bool> isTodayBirthday() async {
    final birthday = await getBirthday();
    if (birthday == null) return false;

    final today = DateTime.now();
    return today.month == birthday.month && today.day == birthday.day;
  }

  // Doğum gününe kaç gün kaldı?
  Future<int?> daysUntilBirthday() async {
    final birthday = await getBirthday();
    if (birthday == null) return null;

    final today = DateTime.now();
    final thisYearBirthday = DateTime(today.year, birthday.month, birthday.day);
    
    if (thisYearBirthday.isBefore(today)) {
      // Bu yıl geçti, gelecek yıl
      final nextYearBirthday = DateTime(today.year + 1, birthday.month, birthday.day);
      return nextYearBirthday.difference(today).inDays;
    } else {
      return thisYearBirthday.difference(today).inDays;
    }
  }

  // Doğum günü mesajı
  Future<String?> getBirthdayMessage() async {
    if (await isTodayBirthday()) {
      return '🎂🎉 DOĞUM GÜNÜN KUTLU OLSUN! 🎈🎁\n\nBu özel günde seni düşünüyorum ve mutluluğun için dua ediyorum! 💜✨';
    }
    
    final daysUntil = await daysUntilBirthday();
    if (daysUntil != null && daysUntil <= 7 && daysUntil > 0) {
      return '🎂 Doğum gününe $daysUntil gün kaldı! Heyecanlı mısın? 🎉';
    }
    
    return null;
  }

  // Özel not kaydet (milestone)
  Future<void> saveMilestone(String title, DateTime date, String? description) async {
    final prefs = await SharedPreferences.getInstance();
    final milestones = prefs.getStringList('milestones') ?? [];
    
    final milestone = {
      'title': title,
      'date': date.toIso8601String(),
      'description': description ?? '',
    }.toString();
    
    milestones.add(milestone);
    await prefs.setStringList('milestones', milestones);
  }

  // Tüm özel günleri getir
  Future<List<Map<String, dynamic>>> getAllMilestones() async {
    final prefs = await SharedPreferences.getInstance();
    final milestones = prefs.getStringList('milestones') ?? [];
    
    // Parse etme (basit implementasyon)
    return [];
  }

  // Yaş hesapla
  Future<int?> getAge() async {
    final birthday = await getBirthday();
    if (birthday == null) return null;

    final today = DateTime.now();
    int age = today.year - birthday.year;
    
    if (today.month < birthday.month || 
        (today.month == birthday.month && today.day < birthday.day)) {
      age--;
    }
    
    return age;
  }
}