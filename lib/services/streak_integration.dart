// ==========================================
// CHAT_SCREEN.DART'A EKLENECEK KODLAR
// ==========================================

// 1. Import ekle (en üste)
import '../services/streak_service.dart';

// 2. State değişkeni ekle (_ChatScreenState class'ına)
final StreakService _streakService = StreakService();
int _currentStreak = 0;

// 3. initState'e ekle (mevcut initState metoduna)
@override
void initState() {
  super.initState();
  initializeDateFormatting('tr_TR', null);
  _loadUserProfile();
  _checkBackendHealth();
  _loadProactiveMessage();
  _updateLastSeen();
  _checkSpecialDays();
  _updateStreak(); // EKLE
}

// 4. Yeni metod ekle (class içine herhangi bir yere)
Future<void> _updateStreak() async {
  final streak = await _streakService.updateStreak();
  setState(() {
    _currentStreak = streak;
  });
}

// 5. AppBar'ı güncelle (mevcut AppBar'ın yerine)
appBar: AppBar(
  backgroundColor: Colors.deepPurple,
  foregroundColor: Colors.white,
  title: Row(
    children: [
      Expanded(
        child: Text(
          _userProfile != null 
              ? 'Dost AI - ${_userProfile!.displayName}' 
              : 'Dost AI'
        ),
      ),
      // Streak badge ekle
      if (_currentStreak > 0) ...[
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: Colors.orange,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('🔥', style: TextStyle(fontSize: 14)),
              const SizedBox(width: 4),
              Text(
                '$_currentStreak',
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 8),
      ],
      Container(
        width: 10,
        height: 10,
        decoration: BoxDecoration(
          color: _isBackendHealthy ? Colors.green : Colors.red,
          shape: BoxShape.circle,
        ),
      ),
    ],
  ),
  actions: [
    IconButton(
      icon: const Icon(Icons.search),
      onPressed: () {
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (context) => const SearchScreen(),
          ),
        );
      },
    ),
    IconButton(
      icon: const Icon(Icons.person),
      onPressed: () {
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (context) => ProfileScreen(),
          ),
        );
      },
    ),
    IconButton(
      icon: const Icon(Icons.refresh),
      onPressed: _checkBackendHealth,
    ),
  ],
),

// ==========================================
// OPSIYONEL: Streak milestone kutlaması
// ==========================================

// İlk mesaj ekranında (proactive message yanına) ekleyebilirsin:
if (_currentStreak >= 7)
  Container(
    margin: const EdgeInsets.symmetric(horizontal: 40, vertical: 10),
    padding: const EdgeInsets.all(15),
    decoration: BoxDecoration(
      gradient: LinearGradient(
        colors: [Colors.orange.shade300, Colors.deepOrange.shade400],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
      borderRadius: BorderRadius.circular(15),
      boxShadow: [
        BoxShadow(
          color: Colors.orange.withOpacity(0.3),
          blurRadius: 10,
          offset: const Offset(0, 4),
        ),
      ],
    ),
    child: Text(
      _streakService.getStreakMessage(_currentStreak),
      textAlign: TextAlign.center,
      style: const TextStyle(
        fontSize: 16,
        fontWeight: FontWeight.bold,
        color: Colors.white,
      ),
    ),
  ),