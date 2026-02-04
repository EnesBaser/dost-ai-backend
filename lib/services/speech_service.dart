import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:permission_handler/permission_handler.dart';

class SpeechService {
  static final SpeechService _instance = SpeechService._internal();
  factory SpeechService() => _instance;
  SpeechService._internal();

  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isInitialized = false;
  bool _isListening = false;

  bool get isListening => _isListening;

  // Servisi başlat
  Future<bool> initialize() async {
    if (_isInitialized) return true;

    try {
      _isInitialized = await _speech.initialize(
        onError: (error) => print('Speech error: $error'),
        onStatus: (status) => print('Speech status: $status'),
      );
      return _isInitialized;
    } catch (e) {
      print('Speech initialization error: $e');
      return false;
    }
  }

  // Mikrofon izni iste
  Future<bool> requestPermission() async {
    final status = await Permission.microphone.request();
    return status.isGranted;
  }

  // Dinlemeye başla
  Future<void> startListening({
    required Function(String) onResult,
    required Function() onListeningComplete,
    bool autoSend = false, // YENİ PARAMETRE
  }) async {
    final hasPermission = await Permission.microphone.request();
    if (!hasPermission.isGranted) return;

    if (!_speech.isAvailable) {
      await initialize();
    }

    await _speech.listen(
      onResult: (result) {
        final text = result.recognizedWords;
        onResult(text);
        
        // YENİ: Konuşma bitince otomatik gönder
        if (autoSend && result.finalResult) {
          onListeningComplete();
        }
      },
      localeId: 'tr_TR',
      listenMode: stt.ListenMode.confirmation,
      cancelOnError: false,
      partialResults: true,
      listenFor: const Duration(seconds: 30),
      pauseFor: const Duration(seconds: 2), // 2 saniye sessizlik = bitir
    );
  }

  // Dinlemeyi durdur
  Future<void> stopListening() async {
    if (_isListening) {
      _isListening = false;
      await _speech.stop();
    }
  }

  // İptal et
  Future<void> cancel() async {
    if (_isListening) {
      _isListening = false;
      await _speech.cancel();
    }
  }

  // Servis durdu mu?
  bool get isAvailable => _speech.isAvailable;
}