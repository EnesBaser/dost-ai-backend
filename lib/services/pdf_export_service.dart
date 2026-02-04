import 'dart:io';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import 'package:intl/intl.dart';
import 'package:path_provider/path_provider.dart';

class PDFExportService {
  // Konuşma geçmişini PDF olarak kaydet
  Future<File?> exportChatHistory({
    required List<Map<String, dynamic>> messages,
    required String userName,
  }) async {
    try {
      final pdf = pw.Document();

      // Tarihe göre grupla
      final groupedMessages = _groupMessagesByDate(messages);

      // PDF sayfaları oluştur
      for (var entry in groupedMessages.entries) {
        final dateStr = entry.key;
        final dateMessages = entry.value;

        pdf.addPage(
          pw.MultiPage(
            pageFormat: PdfPageFormat.a4,
            margin: const pw.EdgeInsets.all(32),
            header: (context) => _buildHeader(userName),
            footer: (context) => _buildFooter(context),
            build: (context) => [
              pw.Text(
                dateStr,
                style: pw.TextStyle(
                  fontSize: 18,
                  fontWeight: pw.FontWeight.bold,
                  color: PdfColors.deepPurple,
                ),
              ),
              pw.SizedBox(height: 16),
              ...dateMessages.map((msg) => _buildMessageBubble(msg)).toList(),
            ],
          ),
        );
      }

      // PDF'i kaydet
      final output = await getApplicationDocumentsDirectory();
      final file = File('${output.path}/dost_ai_${DateTime.now().millisecondsSinceEpoch}.pdf');
      await file.writeAsBytes(await pdf.save());

      return file;
    } catch (e) {
      print('PDF oluşturma hatası: $e');
      return null;
    }
  }

  // PDF'i paylaş
  Future<void> sharePDF({
    required List<Map<String, dynamic>> messages,
    required String userName,
  }) async {
    try {
      final pdf = pw.Document();
      final groupedMessages = _groupMessagesByDate(messages);

      for (var entry in groupedMessages.entries) {
        final dateStr = entry.key;
        final dateMessages = entry.value;

        pdf.addPage(
          pw.MultiPage(
            pageFormat: PdfPageFormat.a4,
            margin: const pw.EdgeInsets.all(32),
            header: (context) => _buildHeader(userName),
            footer: (context) => _buildFooter(context),
            build: (context) => [
              pw.Text(
                dateStr,
                style: pw.TextStyle(
                  fontSize: 18,
                  fontWeight: pw.FontWeight.bold,
                  color: PdfColors.deepPurple,
                ),
              ),
              pw.SizedBox(height: 16),
              ...dateMessages.map((msg) => _buildMessageBubble(msg)).toList(),
            ],
          ),
        );
      }

      // PDF'i paylaş
      await Printing.sharePdf(
        bytes: await pdf.save(),
        filename: 'dost_ai_chat_${DateTime.now().millisecondsSinceEpoch}.pdf',
      );
    } catch (e) {
      print('PDF paylaşma hatası: $e');
    }
  }

  // PDF önizleme
  Future<void> previewPDF({
    required List<Map<String, dynamic>> messages,
    required String userName,
  }) async {
    try {
      final pdf = pw.Document();
      final groupedMessages = _groupMessagesByDate(messages);

      for (var entry in groupedMessages.entries) {
        final dateStr = entry.key;
        final dateMessages = entry.value;

        pdf.addPage(
          pw.MultiPage(
            pageFormat: PdfPageFormat.a4,
            margin: const pw.EdgeInsets.all(32),
            header: (context) => _buildHeader(userName),
            footer: (context) => _buildFooter(context),
            build: (context) => [
              pw.Text(
                dateStr,
                style: pw.TextStyle(
                  fontSize: 18,
                  fontWeight: pw.FontWeight.bold,
                  color: PdfColors.deepPurple,
                ),
              ),
              pw.SizedBox(height: 16),
              ...dateMessages.map((msg) => _buildMessageBubble(msg)).toList(),
            ],
          ),
        );
      }

      // PDF önizleme
      await Printing.layoutPdf(
        onLayout: (PdfPageFormat format) async => pdf.save(),
      );
    } catch (e) {
      print('PDF önizleme hatası: $e');
    }
  }

  // Header oluştur
  pw.Widget _buildHeader(String userName) {
    return pw.Container(
      alignment: pw.Alignment.centerLeft,
      margin: const pw.EdgeInsets.only(bottom: 16),
      padding: const pw.EdgeInsets.all(16),
      decoration: pw.BoxDecoration(
        color: PdfColors.deepPurple,
        borderRadius: const pw.BorderRadius.all(pw.Radius.circular(8)),
      ),
      child: pw.Row(
        mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
        children: [
          pw.Text(
            'Dost AI - $userName',
            style: pw.TextStyle(
              fontSize: 20,
              fontWeight: pw.FontWeight.bold,
              color: PdfColors.white,
            ),
          ),
          pw.Text(
            DateFormat('dd/MM/yyyy HH:mm').format(DateTime.now()),
            style: const pw.TextStyle(
              fontSize: 12,
              color: PdfColors.white,
            ),
          ),
        ],
      ),
    );
  }

  // Footer oluştur
  pw.Widget _buildFooter(pw.Context context) {
    return pw.Container(
      alignment: pw.Alignment.centerRight,
      margin: const pw.EdgeInsets.only(top: 16),
      child: pw.Text(
        'Sayfa ${context.pageNumber} / ${context.pagesCount}  •  Dost AI Sohbet Yedeği',
        style: pw.TextStyle(
          fontSize: 10,
          color: PdfColors.grey600,
        ),
      ),
    );
  }

  // Mesaj baloncuğu oluştur
  pw.Widget _buildMessageBubble(Map<String, dynamic> msg) {
    final isUser = msg['role'] == 'user';
    final timestamp = msg['timestamp'] as DateTime;
    final timeStr = DateFormat('HH:mm').format(timestamp);

    return pw.Container(
      margin: const pw.EdgeInsets.only(bottom: 12),
      alignment: isUser ? pw.Alignment.centerRight : pw.Alignment.centerLeft,
      child: pw.Container(
        constraints: const pw.BoxConstraints(maxWidth: 400),
        padding: const pw.EdgeInsets.all(12),
        decoration: pw.BoxDecoration(
          color: isUser ? PdfColors.deepPurple : PdfColors.grey300,
          borderRadius: const pw.BorderRadius.all(pw.Radius.circular(12)),
        ),
        child: pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Text(
              msg['message'] ?? '',
              style: pw.TextStyle(
                fontSize: 12,
                color: isUser ? PdfColors.white : PdfColors.black,
              ),
            ),
            pw.SizedBox(height: 4),
            pw.Text(
              timeStr,
              style: pw.TextStyle(
                fontSize: 9,
                color: isUser ? PdfColors.grey300 : PdfColors.grey600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Mesajları tarihe göre grupla
  Map<String, List<Map<String, dynamic>>> _groupMessagesByDate(
      List<Map<String, dynamic>> messages) {
    final Map<String, List<Map<String, dynamic>>> grouped = {};

    for (var msg in messages) {
      final timestamp = msg['timestamp'] as DateTime;
      final dateKey = DateFormat('dd MMMM yyyy', 'tr_TR').format(timestamp);

      grouped.putIfAbsent(dateKey, () => []).add(msg);
    }

    return grouped;
  }
}