"""Speech-to-text, used to verify every narration line (did the engine say what the script says?).
providers: sarvam (Indian languages, model saarika), openai (whisper-1 / gpt-4o-transcribe). Paid calls.
usage: python tools/voice/stt.py file.wav [lang]"""
import os, sys, json, uuid, urllib.request, urllib.error
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from keys import key


def _multipart(fields, file_field, path):
    b = uuid.uuid4().hex
    body = b''
    for k, v in fields.items():
        body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    body += f'--{b}\r\nContent-Disposition: form-data; name="{file_field}"; filename="a.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode()
    body += open(path, 'rb').read() + f'\r\n--{b}--\r\n'.encode()
    return body, f'multipart/form-data; boundary={b}'


def stt(path, lang='bn-IN', provider='sarvam', model=None):
    if provider == 'sarvam':
        body, ct = _multipart({'model': model or 'saarika:v2.5', 'language_code': lang}, 'file', path)
        req = urllib.request.Request('https://api.sarvam.ai/speech-to-text', data=body,
                                     headers={'api-subscription-key': key('SARVAM_API_KEY', 'SHARVAM_API_KEY'), 'Content-Type': ct})
        return json.load(urllib.request.urlopen(req, timeout=120)).get('transcript', '')
    if provider == 'openai':
        body, ct = _multipart({'model': model or 'whisper-1', 'language': lang.split('-')[0]}, 'file', path)
        req = urllib.request.Request('https://api.openai.com/v1/audio/transcriptions', data=body,
                                     headers={'Authorization': 'Bearer ' + key('OPENAI_API_KEY'), 'Content-Type': ct})
        return json.load(urllib.request.urlopen(req, timeout=120)).get('text', '')
    raise ValueError(provider)


if __name__ == '__main__':
    print(stt(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'bn-IN'))
