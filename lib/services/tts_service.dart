import 'dart:io';
import 'package:flutter_tts/flutter_tts.dart';

class TTSService {
  static final TTSService _instance = TTSService._internal();
  factory TTSService() => _instance;
  
  TTSService._internal() {
    _initTts();
  }

  final FlutterTts _flutterTts = FlutterTts();
  bool _isSpeaking = false;

  bool get isSpeaking => _isSpeaking;

  Future<void> _initTts() async {
    await _flutterTts.setLanguage('tr-TR');
    await _flutterTts.setSpeechRate(0.45); // Biraz daha yavaş
    await _flutterTts.setVolume(1.0);
    await _flutterTts.setPitch(1.1); // Biraz daha yumuşak

    // Android'de kadın sesi seç (isteğe bağlı)
    if (Platform.isAndroid) {
      try {
        await _flutterTts.setVoice({"name": "tr-tr-x-cfd-network", "locale": "tr-TR"});
      } catch (e) {
        print('⚠️ Ses seçilemedi: $e');
      }
    }

    _flutterTts.setCompletionHandler(() {
      _isSpeaking = false;
      print('✅ Ses çalma tamamlandı');
    });

    _flutterTts.setErrorHandler((msg) {
      _isSpeaking = false;
      print('❌ TTS hata: $msg');
    });
  }

  Future<void> speak(String text) async {
    if (_isSpeaking) {
      await stop();
    }

    try {
      _isSpeaking = true;
      
      // Emojileri temizle
      String cleanText = _removeEmojis(text);
      cleanText = cleanText.trim();
      
      if (cleanText.isEmpty) {
        print('⚠️ Emoji temizlendikten sonra metin boş!');
        _isSpeaking = false;
        return;
      }
      
      print('🔊 TTS konuşuyor: $cleanText');
      await _flutterTts.speak(cleanText);
    } catch (e) {
      print('❌ TTS hata: $e');
      _isSpeaking = false;
    }
  }

  // Emojileri temizle
  String _removeEmojis(String text) {
    return text.replaceAll(
      RegExp(
        r'(\u00a9|\u00ae|[\u2000-\u3300]|\ud83c[\ud000-\udfff]|\ud83d[\ud000-\udfff]|\ud83e[\ud000-\udfff])',
      ),
      '',
    );
  }

  Future<void> stop() async {
    await _flutterTts.stop();
    _isSpeaking = false;
  }

  Future<void> setVolume(double volume) async {
    await _flutterTts.setVolume(volume);
  }

  Future<void> setSpeechRate(double rate) async {
    await _flutterTts.setSpeechRate(rate);
  }

  Future<void> setPitch(double pitch) async {
    await _flutterTts.setPitch(pitch);
  }

  Future<void> dispose() async {
    await _flutterTts.stop();
  }
}