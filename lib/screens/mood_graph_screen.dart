import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import '../../services/chat_history_service.dart';
import '../../services/emotion_service.dart';

class MoodGraphScreen extends StatefulWidget {
  const MoodGraphScreen({super.key});

  @override
  State<MoodGraphScreen> createState() => _MoodGraphScreenState();
}

class _MoodGraphScreenState extends State<MoodGraphScreen> {
  final ChatHistoryService chatHistoryService = ChatHistoryService();
  final EmotionService emotionService = EmotionService();

  List<Map<String, dynamic>> _weeklyData = [];
  bool _isLoading = true;

  int _totalAnalyzed = 0;
  int _totalPositive = 0;
  int _totalNegative = 0;
  int _totalNeutral = 0;
  String _dominantEmotion = 'neutral';

  @override
  void initState() {
    super.initState();
    _loadMoodData();
  }

  Future<void> _loadMoodData() async {
    final allMessages = await chatHistoryService.getAllMessages();
    final now = DateTime.now().toUtc().add(const Duration(hours: 3));

    final List<Map<String, dynamic>> weekData = [];

    for (int i = 6; i >= 0; i--) {
      final date = now.subtract(Duration(days: i));
      int dayPositive = 0;
      int dayNegative = 0;
      int dayNeutral = 0;

      for (var msg in allMessages) {
        if (msg['role'] != 'user') continue;

        final timestamp = DateTime.parse(msg['timestamp'] as String);
        final turkeyTime = timestamp.isUtc
            ? timestamp.add(const Duration(hours: 3))
            : timestamp;

        if (turkeyTime.year == date.year &&
            turkeyTime.month == date.month &&
            turkeyTime.day == date.day) {
          final analysis = emotionService.analyzeEmotion(msg['message']);
          final emotion = analysis['emotion'] as String;

          if (emotion == 'happy') dayPositive++;
          else if (emotion == 'sad') dayNegative++;
          else dayNeutral++;
        }
      }

      weekData.add({
        'date': date,
        'positive': dayPositive,
        'negative': dayNegative,
        'neutral': dayNeutral,
        'total': dayPositive + dayNegative + dayNeutral,
      });

      _totalPositive += dayPositive;
      _totalNegative += dayNegative;
      _totalNeutral += dayNeutral;
    }

    _totalAnalyzed = _totalPositive + _totalNegative + _totalNeutral;

    if (_totalPositive >= _totalNegative && _totalPositive >= _totalNeutral) {
      _dominantEmotion = 'happy';
    } else if (_totalNegative >= _totalPositive && _totalNegative >= _totalNeutral) {
      _dominantEmotion = 'sad';
    } else {
      _dominantEmotion = 'neutral';
    }

    setState(() {
      _weeklyData = weekData;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(
          backgroundColor: Colors.deepPurple,
          foregroundColor: Colors.white,
          title: Text('mood.title'.tr()),
        ),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.deepPurple,
        foregroundColor: Colors.white,
        title: Text('mood.title_emoji'.tr()),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
          _buildSummaryCards(),
          const SizedBox(height: 20),
          Text(
            'mood.last_7_days'.tr(),
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          _buildBarGraph(),
          const SizedBox(height: 24),
          _buildWeeklySummary(),
          const SizedBox(height: 20),
          Text(
            'mood.daily_detail'.tr(),
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          _buildDailyDetails(),
        ],
        ),
      ),
    );
  }

  Widget _buildSummaryCards() {
    final positivePercent = _totalAnalyzed > 0
        ? (_totalPositive / _totalAnalyzed * 100).toStringAsFixed(0)
        : '0';

    return Row(
      children: [
        Expanded(child: _summaryCard('😊', 'mood.positive'.tr(), positivePercent + '%', Colors.green)),
        const SizedBox(width: 10),
        Expanded(child: _summaryCard(_getDominantEmoji(), 'mood.dominant'.tr(), _getDominantLabel(), Colors.deepPurple)),
        const SizedBox(width: 10),
        Expanded(child: _summaryCard('💬', 'mood.analyzed'.tr(), '$_totalAnalyzed', Colors.blue)),
      ],
    );
  }

  Widget _summaryCard(String emoji, String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Text(emoji, style: const TextStyle(fontSize: 24)),
          Text(label, style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.bold)),
          Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color)),
        ],
      ),
    );
  }
  Widget _buildBarGraph() {
    final maxVal = _weeklyData.map((d) => d['total'] as int).fold(0, (a, b) => a > b ? a : b);
    final graphHeight = 160.0;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).brightness == Brightness.dark
            ? const Color(0xFF1E1E1E)
            : Colors.grey[50],
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.grey.withOpacity(0.2)),
      ),
      child: Column(
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: _weeklyData.map((day) {
              final total = day['total'] as int;
              final positive = day['positive'] as int;
              final negative = day['negative'] as int;
              final neutral = day['neutral'] as int;
              final barHeight = maxVal > 0 ? (total / maxVal) * graphHeight : 0.0;
              final date = day['date'] as DateTime;
              final dayName = _getDayName(date);
              final isToday = date.day == DateTime.now().day && date.month == DateTime.now().month;

              return Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (total > 0)
                    Text('$total', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 4),
                  SizedBox(
                    height: graphHeight,
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Container(
                          width: 32,
                          height: barHeight > 0 ? barHeight : 4,
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(6),
                            gradient: LinearGradient(
                              colors: _getBarColor(positive, negative, neutral),
                              begin: Alignment.bottomCenter,
                              end: Alignment.topCenter,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    dayName,
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: isToday ? FontWeight.bold : null,
                      color: isToday ? Colors.deepPurple : null,
                    ),
                  ),
                  if (isToday)
                    const Text('●', style: TextStyle(fontSize: 8, color: Colors.deepPurple)),
                ],
              );
            }).toList(),
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _legendItem('😊 ' + 'mood.positive'.tr(), Colors.green),
              const SizedBox(width: 16),
              _legendItem('😐 ' + 'mood.neutral'.tr(), Colors.grey),
              const SizedBox(width: 16),
              _legendItem('😢 ' + 'mood.negative'.tr(), Colors.red),
            ],
          ),
        ],
      ),
    );
  }

  Widget _legendItem(String label, Color color) {
    return Row(
      children: [
        Container(width: 10, height: 10, decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(3))),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 11)),
      ],
    );
  }

  List<Color> _getBarColor(int positive, int negative, int neutral) {
    if (positive >= negative && positive >= neutral) {
      return [Colors.green, Colors.green.shade300];
    } else if (negative >= positive && negative >= neutral) {
      return [Colors.red, Colors.red.shade300];
    }
    return [Colors.grey, Colors.grey.shade300];
  }

  Widget _buildWeeklySummary() {
    String summaryText = '';
    String summaryEmoji = '';

    final pct = _totalAnalyzed > 0 ? (_totalPositive / _totalAnalyzed * 100) : 0;
    if (pct >= 60) {
      summaryEmoji = '🌟';
      summaryText = 'mood.summary_great'.tr();
    } else if (pct >= 40) {
      summaryEmoji = '😊';
      summaryText = 'mood.summary_balanced'.tr();
    } else {
      summaryEmoji = '💪';
      summaryText = 'mood.summary_tough'.tr();
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.deepPurple.shade100, Colors.deepPurple.shade50],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        children: [
          Text(summaryEmoji, style: const TextStyle(fontSize: 32)),
          const SizedBox(height: 8),
          Text('mood.weekly_summary'.tr(), style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.deepPurple)),
          const SizedBox(height: 4),
          Text(summaryText, textAlign: TextAlign.center, style: const TextStyle(fontSize: 14, color: Colors.deepPurple)),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _statItem('😊', '$_totalPositive', 'mood.positive'.tr()),
              _statItem('😐', '$_totalNeutral', 'mood.neutral'.tr()),
              _statItem('😢', '$_totalNegative', 'mood.negative'.tr()),
            ],
          ),
        ],
      ),
    );
  }

  Widget _statItem(String emoji, String value, String label) {
    return Column(
      children: [
        Text(emoji, style: const TextStyle(fontSize: 20)),
        Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
      ],
    );
  }

  Widget _buildDailyDetails() {
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: _weeklyData.length,
      itemBuilder: (context, index) {
        final day = _weeklyData[index];
        final date = day['date'] as DateTime;
        final total = day['total'] as int;
        final positive = day['positive'] as int;
        final negative = day['negative'] as int;
        final neutral = day['neutral'] as int;
        final isToday = date.day == DateTime.now().day && date.month == DateTime.now().month;

        String emoji = '😐';
        if (total > 0) {
          if (positive >= negative && positive >= neutral) emoji = '😊';
          else if (negative >= positive && negative >= neutral) emoji = '😢';
        }

        return Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: isToday
                ? Colors.deepPurple.withOpacity(0.1)
                : (Theme.of(context).brightness == Brightness.dark ? const Color(0xFF1E1E1E) : Colors.grey[50]),
            borderRadius: BorderRadius.circular(10),
            border: isToday
                ? Border.all(color: Colors.deepPurple, width: 2)
                : Border.all(color: Colors.grey.withOpacity(0.2)),
          ),
          child: Row(
            children: [
              Text(emoji, style: const TextStyle(fontSize: 24)),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          '${date.day} ${_getMonthName(date.month)}',
                          style: TextStyle(fontWeight: FontWeight.bold, color: isToday ? Colors.deepPurple : null),
                        ),
                        if (isToday) ...[
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(color: Colors.deepPurple, borderRadius: BorderRadius.circular(10)),
                            child: Text('common.today'.tr(), style: const TextStyle(fontSize: 10, color: Colors.white)),
                          ),
                        ],
                      ],
                    ),
                    Text(
                      total > 0 ? '😊 $positive  😐 $neutral  😢 $negative' : 'mood.no_messages'.tr(),
                      style: const TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                  ],
                ),
              ),
              if (total > 0) Text('mood.messages_count'.tr(namedArgs: {'count': total.toString()}), style: const TextStyle(fontSize: 11, color: Colors.grey)),
            ],
          ),
        );
      },
    );
  }

  String _getDayName(DateTime date) {
    final days = [
      'mood.days.mon'.tr(),
      'mood.days.tue'.tr(),
      'mood.days.wed'.tr(),
      'mood.days.thu'.tr(),
      'mood.days.fri'.tr(),
      'mood.days.sat'.tr(),
      'mood.days.sun'.tr(),
    ];
    return days[date.weekday - 1];
  }

  String _getMonthName(int month) {
    final months = [
      'mood.months.jan'.tr(),
      'mood.months.feb'.tr(),
      'mood.months.mar'.tr(),
      'mood.months.apr'.tr(),
      'mood.months.may'.tr(),
      'mood.months.jun'.tr(),
      'mood.months.jul'.tr(),
      'mood.months.aug'.tr(),
      'mood.months.sep'.tr(),
      'mood.months.oct'.tr(),
      'mood.months.nov'.tr(),
      'mood.months.dec'.tr(),
    ];
    return months[month - 1];
  }

  String _getDominantEmoji() {
    switch (_dominantEmotion) {
      case 'happy': return '😊';
      case 'sad': return '😢';
      default: return '😐';
    }
  }

  String _getDominantLabel() {
    switch (_dominantEmotion) {
      case 'happy': return 'mood.emotion_happy'.tr();
      case 'sad': return 'mood.emotion_sad'.tr();
      default: return 'mood.emotion_neutral'.tr();
    }
  }
}