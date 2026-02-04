import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import '../../../models/user_profile.dart';
import '../../../services/greeting_service.dart';
import 'package:easy_localization/easy_localization.dart';

class EmptyChatView extends StatelessWidget {
  final UserProfile? userProfile;
  final String? proactiveMessage;
  final GreetingService greetingService;

  const EmptyChatView({
    super.key,
    required this.userProfile,
    required this.proactiveMessage,
    required this.greetingService,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            userProfile != null
                ? greetingService.getTimeBasedGreeting(userProfile!.displayName)
                : 'chat.empty_greeting'.tr(),
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Colors.deepPurple,
            ),
          ),
          const SizedBox(height: 20),
          if (proactiveMessage != null) ...[
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 40),
              padding: const EdgeInsets.all(15),
              decoration: BoxDecoration(
                color: Colors.deepPurple.withOpacity(0.1),
                borderRadius: BorderRadius.circular(15),
                border: Border.all(
                  color: Colors.deepPurple.withOpacity(0.3),
                ),
              ),
              child: Text(
                proactiveMessage!,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 16,
                  color: Colors.deepPurple,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}