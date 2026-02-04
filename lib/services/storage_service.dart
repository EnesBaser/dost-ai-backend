import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../models/user_profile.dart';

class StorageService {
  static const String _userProfileKey = 'user_profile';
  static const String _isFirstLaunchKey = 'is_first_launch';

  // İlk açılış mı kontrolü
  Future<bool> isFirstLaunch() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_isFirstLaunchKey) ?? true;
  }

  // İlk açılışı tamamlandı olarak işaretle
  Future<void> setFirstLaunchComplete() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_isFirstLaunchKey, false);
  }

  // Kullanıcı profilini kaydet
  Future<void> saveUserProfile(UserProfile profile) async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = jsonEncode(profile.toJson());
    await prefs.setString(_userProfileKey, jsonString);
  }

  // Kullanıcı profilini getir
  Future<UserProfile?> getUserProfile() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = prefs.getString(_userProfileKey);
    
    if (jsonString == null) return null;
    
    final json = jsonDecode(jsonString);
    return UserProfile.fromJson(json);
  }

  // Kullanıcı profilini sil ve onboarding'e dön
  Future<void> clearUserProfile() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_userProfileKey);
    await prefs.setBool(_isFirstLaunchKey, true); // İlk açılış flag'ini sıfırla
  }
}