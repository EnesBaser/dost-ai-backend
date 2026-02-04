import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:easy_localization/easy_localization.dart';

class MessageCounter extends StatelessWidget {
  final int todayCount;
  final int weekCount;
  final int totalCount;

  const MessageCounter({
    super.key,
    required this.todayCount,
    required this.weekCount,
    required this.totalCount,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Theme.of(context).brightness == Brightness.dark
            ? const Color(0xFF1E1E1E)
            : Colors.grey[100],
        border: Border(
          top: BorderSide(
            color: Colors.grey.withOpacity(0.3),
            width: 1,
          ),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          _buildStat('counter.today'.tr(), todayCount, Icons.today, Colors.blue),
          const SizedBox(width: 8),
          const Text('•', style: TextStyle(color: Colors.grey)),
          const SizedBox(width: 8),
          _buildStat('counter.week'.tr(), weekCount, Icons.date_range, Colors.green),
          const SizedBox(width: 8),
          const Text('•', style: TextStyle(color: Colors.grey)),
          const SizedBox(width: 8),
          _buildStat('counter.total'.tr(), totalCount, Icons.chat_bubble, Colors.deepPurple),
        ],
      ),
    );
  }

  Widget _buildStat(String label, int count, IconData icon, Color color) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: color),
        const SizedBox(width: 4),
        Text(
          '$label: ',
          style: const TextStyle(
            fontSize: 12,
            color: Colors.grey,
          ),
        ),
        Text(
          '$count',
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ],
    );
  }
}