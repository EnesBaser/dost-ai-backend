class UserProfile {
  final String name;
  final String? nickname; // Nasıl hitap edilmek istediği
  final List<String>? interests; // İlgi alanları
  final DateTime createdAt;

  UserProfile({
    required this.name,
    this.nickname,
    this.interests,
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();

  // JSON'dan model oluşturma
  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      name: json['name'] as String,
      nickname: json['nickname'] as String?,
      interests: json['interests'] != null 
          ? List<String>.from(json['interests']) 
          : null,
      createdAt: DateTime.parse(json['createdAt'] as String),
    );
  }

  // Model'i JSON'a çevirme
  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'nickname': nickname,
      'interests': interests,
      'createdAt': createdAt.toIso8601String(),
    };
  }

  // Hitap şekli (nickname varsa onu kullan, yoksa isim)
  String get displayName => nickname ?? name;
}