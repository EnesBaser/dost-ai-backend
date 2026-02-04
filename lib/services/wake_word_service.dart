import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:permission_handler/permission_handler.dart';

class WakeWordService {
  static final WakeWordService _instance = WakeWordService._internal();
  factory WakeWordService() => _instance;
  WakeWordService._internal();

  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isListening = false;
  bool _isEnabled = false;

  bool get isListening => _isListening;
  bool get isEnabled => _isEnabled;

  // Servisi başlat
  Future<bool> initialize() async {
    try {
      final available = await _speech.initialize(
        onError: (error) => print('Wake word error: $error'),
        onStatus: (status) => print('Wake word status: $status'),
      );
      return available;
    } catch (e) {
      print('Wake word init error: $e');
      return false;
    }
  }

  // Wake word dinlemeyi başlat
  Future<void> startListening({
    required Function() onWakeWordDetected,
    List<String> wakeWords = const ['hey dost', 'hey dostum', 'merhaba dost'],
  }) async {
    final hasPermission = await Permission.microphone.request();
    if (!hasPermission.isGranted) return;

    if (!_speech.isAvailable) {
      await initialize();
    }

    _isEnabled = true;
    _continuousListen(onWakeWordDetected, wakeWords);
  }

  // Sürekli dinle
  Future<void> _continuousListen(
    Function() onWakeWordDetected,
    List<String> wakeWords,
  ) async {
    if (!_isEnabled) return;

    _isListening = true;
    
    await _speech.listen(
      onResult: (result) {
        final text = result.recognizedWords.toLowerCase();
        print('Dinleniyor: $text');

        // Wake word kontrolü
        for (var wakeWord in wakeWords) {
          if (text.contains(wakeWord)) {
            print('Wake word algılandı: $wakeWord');
            onWakeWordDetected();
            return;
          }
        }
      },
      localeId: 'tr_TR',
      listenMode: stt.ListenMode.confirmation,
      cancelOnError: false,
      partialResults: true,
      listenFor: const Duration(seconds: 30),
    );

    // Dinleme bitince tekrar başlat
    await Future.delayed(const Duration(milliseconds: 500));
    if (_isEnabled) {
      _continuousListen(onWakeWordDetected, wakeWords);
    }
  }

  // Durdur
  Future<void> stopListening() async {
    _isEnabled = false;
    _isListening = false;
    await _speech.stop();
  }

  // Toggle
  Future<void> toggle({required Function() onWakeWordDetected}) async {
    if (_isEnabled) {
      await stopListening();
    } else {
      await startListening(onWakeWordDetected: onWakeWordDetected);
    }
  }
}