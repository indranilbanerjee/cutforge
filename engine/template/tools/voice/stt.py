"""Speech-to-text, used to verify every narration line (did the engine say what the script says?).
providers: sarvam (Indian languages) and openai. Paid calls. The model is the registry's choice for latest-stt-<provider>
(tools/resolve_model.py) unless the caller names one, so a vendor's retirement of a model arrives with a registry sync.
usage: python tools/voice/stt.py file.wav [lang]"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import cli; cli.guard(__name__, __file__, __doc__)
import os, sys, json, uuid, urllib.request, urllib.error
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from keys import key
from resolve_model import model_for


def _multipart(fields, file_field, path):
    b = uuid.uuid4().hex
    body = b''
    for k, v in fields.items():
        body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    body += f'--{b}\r\nContent-Disposition: form-data; name="{file_field}"; filename="a.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode()
    body += open(path, 'rb').read() + f'\r\n--{b}--\r\n'.encode()
    return body, f'multipart/form-data; boundary={b}'


def plan_item(provider, seconds, model=None):
    """What spend.plan() needs to quote a transcription of `seconds` of audio."""
    alias, prefix = {'sarvam': ('latest-stt-sarvam', 'https://api.sarvam.ai/'),
                     'openai': ('latest-stt-openai', 'https://api.openai.com/v1/audio/transcriptions')}[provider]
    return {'provider': provider, 'model': model_for(alias, model, prefix), 'unit': 'second', 'units': seconds}


def stt(path, lang='bn-IN', provider='sarvam', model=None):
    if provider == 'sarvam':
        m = model_for('latest-stt-sarvam', model, 'https://api.sarvam.ai/')
        fields = {'model': m, 'language_code': lang}
        if m.startswith('saaras'): fields['mode'] = 'transcribe'      # saaras models take a mode; a plain transcript is "transcribe"
        body, ct = _multipart(fields, 'file', path)
        req = urllib.request.Request('https://api.sarvam.ai/speech-to-text', data=body,
                                     headers={'api-subscription-key': key('SARVAM_API_KEY', 'SHARVAM_API_KEY'), 'Content-Type': ct})
        return json.load(urllib.request.urlopen(req, timeout=120)).get('transcript', '')
    if provider == 'openai':
        body, ct = _multipart({'model': model_for('latest-stt-openai', model, 'https://api.openai.com/v1/audio/transcriptions'),
                               'language': lang.split('-')[0]}, 'file', path)
        req = urllib.request.Request('https://api.openai.com/v1/audio/transcriptions', data=body,
                                     headers={'Authorization': 'Bearer ' + key('OPENAI_API_KEY'), 'Content-Type': ct})
        return json.load(urllib.request.urlopen(req, timeout=120)).get('text', '')
    raise ValueError(provider)


if __name__ == '__main__':
    print(stt(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'bn-IN'))
