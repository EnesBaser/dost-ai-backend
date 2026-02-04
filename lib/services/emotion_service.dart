class EmotionService {
  static final EmotionService _instance = EmotionService._internal();
  factory EmotionService() => _instance;
  EmotionService._internal();

  // Mesajdan duygu analizi (basit keyword-based)
  Map<String, dynamic> analyzeEmotion(String message) {
    final lowerMessage = message.toLowerCase();
    
    // Pozitif kelimeler
    final positiveKeywords = [
      'mutlu', 'harika', 'güzel', 'mükemmel', 'süper', 'şahane',
      'iyi', 'keyifli', 'eğlenceli', 'başarılı', 'sevinçli',
      'teşekkür', 'sağol', 'sevindim', 'heyecanlı', 'memnun'
    ];
    
    // Negatif kelimeler
    final negativeKeywords = [
      'üzgün', 'kötü', 'berbat', 'yorgun', 'mutsuz', 'sıkıldı',
      'stresli', 'endişeli', 'kaygılı', 'sinirli', 'kızgın',
      'yalnız', 'boş', 'anlamsız', 'zor', 'problem', 'sorun'
    ];
    
    // Soru işaretleri (yardım istiyor)
    final helpKeywords = [
      'yardım', 'ne yapmalı', 'bilmiyorum', 'emin değil',
      'kararsız', 'şaşkın', 'ne yapacağım'
    ];
    
    int positiveScore = 0;
    int negativeScore = 0;
    int helpScore = 0;
    
    // Skorlama
    for (var keyword in positiveKeywords) {
      if (lowerMessage.contains(keyword)) positiveScore++;
    }
    
    for (var keyword in negativeKeywords) {
      if (lowerMessage.contains(keyword)) negativeScore++;
    }
    
    for (var keyword in helpKeywords) {
      if (lowerMessage.contains(keyword)) helpScore++;
    }
    
    // Emoji analizi
    if (lowerMessage.contains('😊') || lowerMessage.contains('😄') || 
        lowerMessage.contains('🎉') || lowerMessage.contains('💜')) {
      positiveScore += 2;
    }
    
    if (lowerMessage.contains('😢') || lowerMessage.contains('😔') || 
        lowerMessage.contains('😞')) {
      negativeScore += 2;
    }
    
    // Duygu belirleme
    String emotion = 'neutral';
    String response = '';
    
    if (negativeScore > positiveScore) {
      emotion = 'sad';
      response = 'Üzgün görünüyorsun. Anlatmak ister misin? 💜';
    } else if (positiveScore > negativeScore) {
      emotion = 'happy';
      response = 'Mutlu görünüyorsun! Bu harika! 😊';
    } else if (helpScore > 0) {
      emotion = 'confused';
      response = 'Kafan karışık gibi. Konuşarak açıklık getirebiliriz! 🤔';
    }
    
    return {
      'emotion': emotion,
      'positiveScore': positiveScore,
      'negativeScore': negativeScore,
      'helpScore': helpScore,
      'suggestedResponse': response,
    };
  }

  // Duygusal yanıt önerisi
  String getEmotionalResponse(String emotion) {
    switch (emotion) {
      case 'sad':
        return 'Yanındayım, her zaman. Konuşmak seni rahatlatabilir. 💜';
      case 'happy':
        return 'Seninle mutlu olmak güzel! 🌟';
      case 'confused':
        return 'Birlikte düşünelim, çözüm buluruz! 💭';
      case 'angry':
        return 'Derin bir nefes al, ben buradayım. 🌸';
      default:
        return '';
    }
  }

  // Emoji'ye göre duygu
  String getEmotionFromEmoji(String message) {
    if (message.contains('❤️') || message.contains('💜') || message.contains('😍')) {
      return 'love';
    } else if (message.contains('😂') || message.contains('🤣')) {
      return 'laughing';
    } else if (message.contains('😢') || message.contains('😭')) {
      return 'crying';
    } else if (message.contains('😡') || message.contains('😠')) {
      return 'angry';
    }
    return 'neutral';
  }
}