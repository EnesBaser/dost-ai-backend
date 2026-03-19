# routes/websocket.py
import json
import base64
import threading
from flask import request
import websocket as ws_client
from config import OPENAI_API_KEY


def register_websocket(sock):
    """Sock objesi app.py'den geçirilir."""

    @sock.route('/ws/realtime')
    def realtime_ws(ws):
        device_id = request.args.get('device_id', '')
        if not device_id:
            ws.send(json.dumps({'type': 'error', 'message': 'Device ID required'}))
            return

        if not OPENAI_API_KEY:
            ws.send(json.dumps({'type': 'error', 'message': 'API key not configured'}))
            return

        openai_ws     = None
        system_prompt = "Sen DostAI'sin, Turkce konusan kisisel yapay zeka dostusun."

        try:
            openai_ws = ws_client.create_connection(
                'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview',
                header=[
                    f'Authorization: Bearer {OPENAI_API_KEY}',
                    'OpenAI-Beta: realtime=v1',
                ]
            )
            openai_ws.send(json.dumps({
                'type': 'session.update',
                'session': {
                    'modalities':               ['text', 'audio'],
                    'instructions':             system_prompt,
                    'voice':                    'alloy',
                    'input_audio_format':       'pcm16',
                    'output_audio_format':      'pcm16',
                    'input_audio_transcription': {'model': 'whisper-1'},
                    'turn_detection':           None,
                    'temperature':              0.8,
                }
            }))

            def forward_from_openai():
                transcript_buffer = ""
                try:
                    while True:
                        msg = openai_ws.recv()
                        if not msg:
                            break
                        data       = json.loads(msg)
                        event_type = data.get('type', '')

                        if event_type == 'conversation.item.input_audio_transcription.completed':
                            transcript = data.get('transcript', '')
                            if transcript:
                                ws.send(json.dumps({'type': 'transcript', 'text': transcript}))
                                try:
                                    openai_ws.send(json.dumps({
                                        'type': 'conversation.item.create',
                                        'item': {
                                            'type': 'message', 'role': 'user',
                                            'content': [{'type': 'input_text', 'text': transcript}],
                                        }
                                    }))
                                    openai_ws.send(json.dumps({'type': 'response.create'}))
                                except Exception as te:
                                    print(f'❌ Text gönderme hatası: {te}', flush=True)

                        elif event_type == 'response.audio_transcript.delta':
                            transcript_buffer += data.get('delta', '')

                        elif event_type == 'response.audio_transcript.done':
                            if transcript_buffer:
                                ws.send(json.dumps({'type': 'ai_text', 'text': transcript_buffer}))
                                transcript_buffer = ""

                        elif event_type in ('response.audio.delta', 'response.output_audio.delta'):
                            audio = data.get('delta', '')
                            if audio:
                                ws.send(json.dumps({'type': 'ai_audio', 'audio': audio}))

                        elif event_type in ('response.audio.done', 'response.output_audio.done'):
                            ws.send(json.dumps({'type': 'audio_done'}))

                        elif event_type == 'error':
                            err = data.get('error', {})
                            ws.send(json.dumps({'type': 'error', 'message': str(err)}))

                except Exception as e:
                    print(f'❌ OpenAI forward error: {e}', flush=True)

            t = threading.Thread(target=forward_from_openai, daemon=True)
            t.start()

            while True:
                msg = ws.receive()
                if msg is None:
                    break
                data     = json.loads(msg)
                msg_type = data.get('type', '')

                if msg_type == 'session.setup':
                    system_prompt = data.get('system_prompt', system_prompt)
                    openai_ws.send(json.dumps({
                        'type':    'session.update',
                        'session': {'instructions': system_prompt},
                    }))

                elif msg_type == 'audio_input':
                    audio_b64 = data.get('audio', '')
                    try:
                        wav_bytes = base64.b64decode(audio_b64)
                        if len(wav_bytes) > 44:
                            pcm_bytes = wav_bytes[44:]
                            pcm_b64   = base64.b64encode(pcm_bytes).decode()
                            openai_ws.send(json.dumps({
                                'type':  'input_audio_buffer.append',
                                'audio': pcm_b64,
                            }))
                    except Exception as ae:
                        print(f'❌ Audio error: {ae}', flush=True)

                elif msg_type == 'audio_commit':
                    try:
                        openai_ws.send(json.dumps({'type': 'input_audio_buffer.commit'}))
                    except Exception as ce:
                        print(f'❌ Commit error: {ce}', flush=True)

        except Exception as e:
            print(f'❌ WebSocket error: {e}', flush=True)
            try:
                ws.send(json.dumps({'type': 'error', 'message': str(e)}))
            except Exception:
                pass
        finally:
            if openai_ws:
                try:
                    openai_ws.close()
                except Exception:
                    pass
