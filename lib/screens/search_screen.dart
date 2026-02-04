import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:easy_localization/easy_localization.dart' as easy;
import '../services/chat_history_service.dart';
import '../services/achievements_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ChatHistoryService _historyService = ChatHistoryService();
  
  List<Map<String, dynamic>> _searchResults = [];
  bool _isSearching = false;
  Map<String, int>? _statistics;

  bool _isLocaleInitialized = false;

  @override
  void initState() {
    super.initState();
    _initialize();
    _checkSearchAchievement();
  }

  Future<void> _initialize() async {
    await initializeDateFormatting('tr_TR', null);
    setState(() {
      _isLocaleInitialized = true;
    });
    _loadStatistics();
  }

  Future<void> _checkSearchAchievement() async {
    try {
      final achievementsService = AchievementsService();
      final prefs = await SharedPreferences.getInstance();
      final hasSearched = prefs.getBool('has_searched') ?? false;
      
      if (!hasSearched) {
        await prefs.setBool('has_searched', true);
        await achievementsService.unlockSpecial('search_first');
      }
    } catch (e) {
      print('Search achievement error: $e');
    }
  }

  Future<void> _loadStatistics() async {
    final stats = await _historyService.getStatistics();
    setState(() {
      _statistics = stats;
    });
  }

  Future<void> _search(String query) async {
    if (query.isEmpty) {
      setState(() {
        _searchResults = [];
        _isSearching = false;
      });
      return;
    }

    setState(() {
      _isSearching = true;
    });

    print('🔍 Searching for: $query');
    final results = await _historyService.searchMessages(query);
    print('📊 Found ${results.length} results');
    
    setState(() {
      _searchResults = results;
      _isSearching = false;
    });
  }

  Future<void> _showTodayMessages() async {
    setState(() {
      _isSearching = true;
    });
    
    final messages = await _historyService.getTodayMessages();
    
    setState(() {
      _searchResults = messages;
      _isSearching = false;
    });
  }

  Future<void> _showThisWeekMessages() async {
    setState(() {
      _isSearching = true;
    });
    
    final messages = await _historyService.getThisWeekMessages();
    
    setState(() {
      _searchResults = messages;
      _isSearching = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('search.title'.tr()),
        backgroundColor: Colors.deepPurple,
        foregroundColor: Colors.white,
      ),
      body: Column(
        children: [
          // Arama kutusu
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'search.hint'.tr(),
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _searchController.clear();
                          _search('');
                        },
                      )
                    : null,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(25),
                ),
              ),
              onChanged: _search,
            ),
          ),

          // İstatistikler
          if (_statistics != null && _searchResults.isEmpty)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      Text(
                        'search.statistics'.tr(),
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _buildStatCard(
                            'search.stat_total'.tr(),
                            '${_statistics!['total']}',
                            Colors.blue,
                          ),
                          _buildStatCard(
                            'search.stat_user'.tr(),
                            '${_statistics!['user']}',
                            Colors.deepPurple,
                          ),
                          _buildStatCard(
                            'search.stat_ai'.tr(),
                            '${_statistics!['ai']}',
                            Colors.green,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),

          // Hızlı filtreler
          if (_searchResults.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _showTodayMessages,
                      icon: const Icon(Icons.today),
                      label: Text('search.filter_today'.tr()),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _showThisWeekMessages,
                      icon: const Icon(Icons.date_range),
                      label: Text('search.filter_week'.tr()),
                    ),
                  ),
                ],
              ),
            ),

          // Arama sonuçları
          Expanded(
            child: !_isLocaleInitialized
                ? const Center(child: CircularProgressIndicator())
                : _searchResults.isEmpty
                    ? (_isSearching
                        ? const Center(child: CircularProgressIndicator())
                        : Center(
                            child: Text(
                              'search.empty_state'.tr(),
                              textAlign: TextAlign.center,
                              style: const TextStyle(color: Colors.grey),
                            ),
                          ))
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _searchResults.length,
                        itemBuilder: (context, index) {
                          final msg = _searchResults[index];
                          final isUser = msg['role'] == 'user';
                          final timestamp = DateTime.parse(msg['timestamp']);
                          final dateStr = DateFormat('dd MMM yyyy, HH:mm', 'tr_TR').format(timestamp);

                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            child: ListTile(
                              leading: CircleAvatar(
                                backgroundColor: isUser
                                    ? Colors.deepPurple
                                    : Colors.grey[300],
                                child: Icon(
                                  isUser ? Icons.person : Icons.smart_toy,
                                  color: isUser ? Colors.white : Colors.grey[700],
                                ),
                              ),
                              title: Text(
                                msg['message'],
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                              subtitle: Text(
                                dateStr,
                                style: const TextStyle(fontSize: 12),
                              ),
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard(String label, String value, Color color) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            color: Colors.grey,
          ),
        ),
      ],
    );
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }
}