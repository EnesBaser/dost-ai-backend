import 'package:flutter/material.dart';

enum AvatarEmotion { happy, sad, neutral, thinking }

class DostAvatar extends StatefulWidget {
  final AvatarEmotion emotion;
  final bool isLoading;
  final double size;

  const DostAvatar({
    super.key,
    this.emotion = AvatarEmotion.neutral,
    this.isLoading = false,
    this.size = 60,
  });

  @override
  State<DostAvatar> createState() => _DostAvatarState();
}

class _DostAvatarState extends State<DostAvatar>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.06).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _pulseAnimation,
      builder: (context, child) {
        return Transform.scale(
          scale: _pulseAnimation.value,
          child: SizedBox(
            width: widget.size,  // DEĞIŞTI: 100 → widget.size
            height: widget.size, // DEĞIŞTI: 100 → widget.size
            child: CustomPaint(
              painter: _AvatarPainter(
                emotion: widget.isLoading ? AvatarEmotion.thinking : widget.emotion,
              ),
              child: widget.isLoading
                  ? Center(
                      child: _ThinkingDots(size: widget.size), // DEĞIŞTI: size parametresi eklendi
                    )
                  : null,
            ),
          ),
        );
      },
    );
  }
}

class _AvatarPainter extends CustomPainter {
  final AvatarEmotion emotion;

  _AvatarPainter({required this.emotion});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 4;

    // Glow shadow
    final shadowPaint = Paint()
      ..color = Colors.deepPurple.withOpacity(0.25)
      ..maskFilter = const MaskFilter.blur(BlurStyle.outer, 8);
    canvas.drawCircle(center, radius, shadowPaint);

    // Background circle gradient
    final bgPaint = Paint()
      ..shader = LinearGradient(
        colors: _getBackgroundColors(),
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ).createShader(Rect.fromCircle(center: center, radius: radius));
    canvas.drawCircle(center, radius, bgPaint);

    // Border
    final borderPaint = Paint()
      ..color = Colors.white.withOpacity(0.3)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;
    canvas.drawCircle(center, radius, borderPaint);

    // Eyes
    _drawEyes(canvas, center, size);

    // Mouth
    _drawMouth(canvas, center, size);

    // Cheek blush (happy/sad)
    if (emotion == AvatarEmotion.happy || emotion == AvatarEmotion.sad) {
      _drawCheeks(canvas, center, size);
    }
  }

  List<Color> _getBackgroundColors() {
    switch (emotion) {
      case AvatarEmotion.happy:
        return [Colors.deepPurple.shade300, Colors.purple.shade400];
      case AvatarEmotion.sad:
        return [Colors.deepPurple.shade600, Colors.indigo.shade700];
      case AvatarEmotion.thinking:
        return [Colors.deepPurple.shade400, Colors.teal.shade500];
      default:
        return [Colors.deepPurple.shade400, Colors.purple.shade500];
    }
  }

  void _drawEyes(Canvas canvas, Offset center, Size size) {
    final eyePaint = Paint()..color = Colors.white;
    final pupilPaint = Paint()..color = Colors.deepPurple.shade900;

    final eyeY = center.dy - size.height * 0.1;
    final leftEyeX = center.dx - size.width * 0.18;
    final rightEyeX = center.dx + size.width * 0.18;

    if (emotion == AvatarEmotion.thinking) {
      canvas.drawCircle(Offset(leftEyeX, eyeY), 6, eyePaint);
      canvas.drawCircle(Offset(leftEyeX, eyeY + 1), 3, pupilPaint);
      final arcPaint = Paint()
        ..color = Colors.white
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.5
        ..strokeCap = StrokeCap.round;
      canvas.drawArc(
        Rect.fromCircle(center: Offset(rightEyeX, eyeY), radius: 5),
        0, -3.14, false, arcPaint,
      );
    } else if (emotion == AvatarEmotion.sad) {
      canvas.drawCircle(Offset(leftEyeX, eyeY), 5, eyePaint);
      canvas.drawCircle(Offset(leftEyeX, eyeY + 1), 2.5, pupilPaint);
      canvas.drawCircle(Offset(rightEyeX, eyeY), 5, eyePaint);
      canvas.drawCircle(Offset(rightEyeX, eyeY + 1), 2.5, pupilPaint);
      final browPaint = Paint()
        ..color = Colors.white.withOpacity(0.8)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2
        ..strokeCap = StrokeCap.round;
      canvas.drawLine(
        Offset(leftEyeX - 7, eyeY - 10),
        Offset(leftEyeX + 5, eyeY - 7),
        browPaint,
      );
      canvas.drawLine(
        Offset(rightEyeX + 7, eyeY - 10),
        Offset(rightEyeX - 5, eyeY - 7),
        browPaint,
      );
    } else {
      canvas.drawCircle(Offset(leftEyeX, eyeY), 6, eyePaint);
      canvas.drawCircle(Offset(leftEyeX, eyeY + 1), 3, pupilPaint);
      canvas.drawCircle(Offset(rightEyeX, eyeY), 6, eyePaint);
      canvas.drawCircle(Offset(rightEyeX, eyeY + 1), 3, pupilPaint);

      if (emotion == AvatarEmotion.happy) {
        canvas.drawCircle(Offset(leftEyeX - 1, eyeY - 1), 1.5, Paint()..color = Colors.white);
        canvas.drawCircle(Offset(rightEyeX - 1, eyeY - 1), 1.5, Paint()..color = Colors.white);
      }
    }
  }

  void _drawMouth(Canvas canvas, Offset center, Size size) {
    final mouthPaint = Paint()
      ..color = Colors.white.withOpacity(0.9)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5
      ..strokeCap = StrokeCap.round;

    final mouthY = center.dy + size.height * 0.15;
    final mouthWidth = size.width * 0.18;

    switch (emotion) {
      case AvatarEmotion.happy:
        canvas.drawArc(
          Rect.fromLTRB(
            center.dx - mouthWidth,
            mouthY - 8,
            center.dx + mouthWidth,
            mouthY + 8,
          ),
          0, 3.14, false, mouthPaint,
        );
        break;
      case AvatarEmotion.sad:
        canvas.drawArc(
          Rect.fromLTRB(
            center.dx - mouthWidth,
            mouthY - 4,
            center.dx + mouthWidth,
            mouthY + 4,
          ),
          3.14, 3.14, false, mouthPaint,
        );
        break;
      case AvatarEmotion.thinking:
        canvas.drawCircle(Offset(center.dx, mouthY), 2.5, Paint()..color = Colors.white.withOpacity(0.9));
        break;
      default:
        canvas.drawLine(
          Offset(center.dx - mouthWidth * 0.7, mouthY),
          Offset(center.dx + mouthWidth * 0.7, mouthY),
          mouthPaint,
        );
        break;
    }
  }

  void _drawCheeks(Canvas canvas, Offset center, Size size) {
    final cheekPaint = Paint()
      ..color = (emotion == AvatarEmotion.happy ? Colors.pink : Colors.blue).withOpacity(0.25);

    final cheekY = center.dy + size.height * 0.05;
    canvas.drawCircle(Offset(center.dx - size.width * 0.22, cheekY), 8, cheekPaint);
    canvas.drawCircle(Offset(center.dx + size.width * 0.22, cheekY), 8, cheekPaint);
  }

  @override
  bool shouldRepaint(covariant _AvatarPainter oldDelegate) {
    return oldDelegate.emotion != emotion;
  }
}

class _ThinkingDots extends StatefulWidget {
  final double size; // YENİ PARAMETRE

  const _ThinkingDots({required this.size}); // YENİ PARAMETRE

  @override
  State<_ThinkingDots> createState() => _ThinkingDotsState();
}

class _ThinkingDotsState extends State<_ThinkingDots>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final dotSize = widget.size * 0.08; // DEĞIŞTI: Nokta boyutu dinamik

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: List.generate(3, (index) {
            final delay = index * 0.2;
            final progress = (_controller.value - delay).clamp(0.0, 1.0);
            final scale = progress < 0.5
                ? Tween<double>(begin: 0.5, end: 1.0).transform(progress * 2)
                : Tween<double>(begin: 1.0, end: 0.5).transform((progress - 0.5) * 2);
            return Transform.scale(
              scale: scale,
              child: Container(
                width: dotSize,  // DEĞIŞTI: size → dotSize
                height: dotSize, // DEĞIŞTI: size → dotSize
                margin: const EdgeInsets.symmetric(horizontal: 2),
                decoration: const BoxDecoration(
                  color: Colors.white,
                  shape: BoxShape.circle,
                ),
              ),
            );
          }),
        );
      },
    );
  }
}