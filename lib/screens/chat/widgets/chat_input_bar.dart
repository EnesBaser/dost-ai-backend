import 'package:flutter/material.dart';
import 'wave_animation.dart';
import 'package:easy_localization/easy_localization.dart';

class ChatInputBar extends StatelessWidget {
  final TextEditingController messageController;
  final bool isListening;
  final bool isLoading;
  final VoidCallback onSend;
  final VoidCallback onStartListening;
  final VoidCallback onStopListening;

  const ChatInputBar({
    super.key,
    required this.messageController,
    required this.isListening,
    required this.isLoading,
    required this.onSend,
    required this.onStartListening,
    required this.onStopListening,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Theme.of(context).brightness == Brightness.dark
            ? const Color(0xFF1E1E1E)
            : Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.3),
            blurRadius: 5,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: isListening ? Colors.red : Colors.grey[300],
            child: IconButton(
              icon: Icon(
                isListening ? Icons.mic : Icons.mic_none,
                color: isListening ? Colors.white : Colors.grey[700],
              ),
              onPressed: isListening ? onStopListening : onStartListening,
            ),
          ),
          const SizedBox(width: 10),
          if (isListening)
            const Expanded(child: WaveAnimation()),
          if (!isListening)
            Expanded(
              child: TextField(
                controller: messageController,
                style: TextStyle(
                  color: Theme.of(context).brightness == Brightness.dark
                      ? Colors.white
                      : Colors.black,
                ),
                decoration: InputDecoration(
                  hintText: 'chat.input_hint'.tr(),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(25),
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 10,
                  ),
                ),
                onSubmitted: (_) => onSend(),
              ),
            ),
          const SizedBox(width: 10),
          CircleAvatar(
            backgroundColor: Colors.deepPurple,
            child: IconButton(
              icon: const Icon(Icons.send, color: Colors.white),
              onPressed: isLoading || isListening ? null : onSend,
            ),
          ),
        ],
      ),
    );
  }
}