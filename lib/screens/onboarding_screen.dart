import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import '../models/user_profile.dart';
import '../services/storage_service.dart';
import 'chat/chat_screen.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  final StorageService _storageService = StorageService();
  
  int _currentPage = 0;
  String _name = '';
  String _nickname = '';
  List<String> _selectedInterests = [];

  List<String> get _interestOptions => [
    'onboarding.interests.tech'.tr(),
    'onboarding.interests.sports'.tr(),
    'onboarding.interests.music'.tr(),
    'onboarding.interests.movies'.tr(),
    'onboarding.interests.books'.tr(),
    'onboarding.interests.travel'.tr(),
    'onboarding.interests.food'.tr(),
    'onboarding.interests.art'.tr(),
    'onboarding.interests.games'.tr(),
    'onboarding.interests.science'.tr(),
  ];

  void _nextPage() {
    if (_currentPage < 4) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      _completeOnboarding();
    }
  }

  void _previousPage() {
    if (_currentPage > 0) {
      _pageController.previousPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }

  Future<void> _completeOnboarding() async {
    if (_name.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('onboarding.name_hint'.tr())),
      );
      return;
    }

    final profile = UserProfile(
      name: _name.trim(),
      nickname: _nickname.trim().isEmpty ? null : _nickname.trim(),
      interests: _selectedInterests.isEmpty ? null : _selectedInterests,
    );

    await _storageService.saveUserProfile(profile);
    await _storageService.setFirstLaunchComplete();

    if (mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (context) => const ChatScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Progress indicator
            Padding(
              padding: const EdgeInsets.all(20),
              child: Row(
                children: List.generate(5, (index) {
                  return Expanded(
                    child: Container(
                      height: 4,
                      margin: const EdgeInsets.symmetric(horizontal: 2),
                      decoration: BoxDecoration(
                        color: index <= _currentPage
                            ? Colors.deepPurple
                            : Colors.grey[300],
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  );
                }),
              ),
            ),

            // Pages
            Expanded(
              child: PageView(
                controller: _pageController,
                onPageChanged: (page) {
                  setState(() => _currentPage = page);
                },
                children: [
                  _buildWelcomePage(),
                  _buildNamePage(),
                  _buildNicknamePage(),
                  _buildInterestsPage(),
                  _buildReadyPage(),
                ],
              ),
            ),

            // Navigation buttons
            Padding(
              padding: const EdgeInsets.all(20),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  if (_currentPage > 0)
                    TextButton(
                      onPressed: _previousPage,
                      child: Text('common.back'.tr()),
                    )
                  else
                    const SizedBox(width: 80),
                  ElevatedButton(
                    onPressed: _nextPage,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.deepPurple,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 40,
                        vertical: 15,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(25),
                      ),
                    ),
                    child: Text(
                      _currentPage == 4 ? 'common.start'.tr() : 'common.continue'.tr(),
                      style: const TextStyle(fontSize: 16),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWelcomePage() {
    return Padding(
      padding: const EdgeInsets.all(30),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            'onboarding.welcome_emoji'.tr(),
            style: const TextStyle(fontSize: 80),
          ),
          const SizedBox(height: 30),
          Text(
            'onboarding.welcome_title'.tr(),
            style: const TextStyle(
              fontSize: 36,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 20),
          Text(
            'onboarding.welcome_message'.tr(),
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey[700],
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNamePage() {
    return Padding(
      padding: const EdgeInsets.all(30),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text(
            '😊',
            style: TextStyle(fontSize: 60),
          ),
          const SizedBox(height: 30),
          Text(
            'onboarding.name_question'.tr(),
            style: const TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 40),
          TextField(
            onChanged: (value) => setState(() => _name = value),
            decoration: InputDecoration(
              hintText: 'onboarding.name_hint'.tr(),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(15),
              ),
              prefixIcon: const Icon(Icons.person),
            ),
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 18),
          ),
        ],
      ),
    );
  }

  Widget _buildNicknamePage() {
    return Padding(
      padding: const EdgeInsets.all(30),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text(
            '💬',
            style: TextStyle(fontSize: 60),
          ),
          const SizedBox(height: 30),
          Text(
            'onboarding.nickname_greeting'.tr(namedArgs: {'name': _name.isEmpty ? '' : _name}),
            style: const TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 20),
          Text(
            'onboarding.nickname_question'.tr(),
            style: TextStyle(
              fontSize: 18,
              color: Colors.grey[700],
            ),
          ),
          const SizedBox(height: 40),
          TextField(
            onChanged: (value) => setState(() => _nickname = value),
            decoration: InputDecoration(
              hintText: 'onboarding.nickname_hint'.tr(namedArgs: {'name': _name.isEmpty ? '' : _name}),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(15),
              ),
              prefixIcon: const Icon(Icons.chat_bubble),
            ),
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 18),
          ),
          const SizedBox(height: 20),
          Text(
            'onboarding.nickname_skip'.tr(namedArgs: {'name': _name}),
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[600],
              fontStyle: FontStyle.italic,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInterestsPage() {
    return Padding(
      padding: const EdgeInsets.all(30),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text(
            '🎯',
            style: TextStyle(fontSize: 60),
          ),
          const SizedBox(height: 30),
          Text(
            'onboarding.interests_question'.tr(),
            style: const TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            'onboarding.interests_subtitle'.tr(),
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 40),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            alignment: WrapAlignment.center,
            children: _interestOptions.map((interest) {
              final isSelected = _selectedInterests.contains(interest);
              return FilterChip(
                label: Text(interest),
                selected: isSelected,
                onSelected: (selected) {
                  setState(() {
                    if (selected) {
                      _selectedInterests.add(interest);
                    } else {
                      _selectedInterests.remove(interest);
                    }
                  });
                },
                selectedColor: Colors.deepPurple.withOpacity(0.3),
                checkmarkColor: Colors.deepPurple,
              );
            }).toList(),
          ),
          const SizedBox(height: 20),
          Text(
            'onboarding.interests_skip'.tr(),
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[600],
              fontStyle: FontStyle.italic,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildReadyPage() {
    final displayName = _nickname.isEmpty ? _name : _nickname;
    
    return Padding(
      padding: const EdgeInsets.all(30),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text(
            '🚀',
            style: TextStyle(fontSize: 80),
          ),
          const SizedBox(height: 30),
          Text(
            'onboarding.ready_title'.tr(),
            style: const TextStyle(
              fontSize: 36,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 20),
          Text(
            'onboarding.ready_message'.tr(namedArgs: {'name': displayName}),
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey[700],
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }
}