"""Text-to-speech providers behind one call:  tts(out_wav, text, voice_cfg, pace=1.0, direction='')
voice_cfg comes from film/script.json "voice": {"provider": ..., "voice": ..., "model": ..., "lang": ...}

providers
  sarvam        Sarvam (Indian languages). voice = speaker name, which must match the model
  sarvam_clone  Sarvam cloned voice. voice = the clone's voice id. ONLY with the voice owner's own consent.
  elevenlabs    ElevenLabs. voice = voice_id
  openai        OpenAI speech. voice = a voice name; `direction` is sent as instructions. The registry's current OpenAI
                text-to-speech model runs only on the Realtime API, which this tool does not call: with no "model" in the voice
                settings this provider refuses and says why. A "model" you name yourself still works until OpenAI shuts the
                /v1/audio/speech endpoint down (2027-01-06 per the registry).
  placeholder   no audio service: writes silence of the estimated length so timing, captions and the mix work early
"model" in the voice settings is optional: without it the model is the registry's choice for latest-tts-<provider>
(tools/resolve_model.py), so a shutdown or a new default arrives with a registry sync, not a code edit.
Keys (env or key file): SARVAM_API_KEY (alias SHARVAM_API_KEY), ELEVENLABS_API_KEY, OPENAI_API_KEY.
APIs change: if a provider errors, read its current docs before changing anything else (field names drift).
Every call here is a paid call except placeholder: the caller must pass the quote gate (tools/spend.py plan())."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import cli; cli.guard(__name__, __file__, __doc__)
import os, sys, json, base64, uuid, urllib.request, urllib.error, io
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from keys import key
from resolve_model import model_for

SR = 48000


def _post(url, body, headers, timeout=180):
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        return urllib.request.urlopen(req, timeout=timeout).read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'{url} -> HTTP {e.code}: {e.read()[:300]!r}') from None


def _to_wav(raw, out, sr_hint=None):
    """Write provider audio (wav bytes, or raw 16-bit PCM when sr_hint is given) to a 48 kHz mono wav."""
    if sr_hint:
        y = np.frombuffer(raw, np.int16).astype(np.float32) / 32768; sr = sr_hint
    else:
        y, sr = sf.read(io.BytesIO(raw), dtype='float32')
    if y.ndim > 1: y = y.mean(1)
    if sr != SR:
        n = int(round(len(y) * SR / sr)); y = np.interp(np.linspace(0, len(y) - 1, n), np.arange(len(y)), y).astype(np.float32)
    sf.write(out, y, SR, subtype='PCM_16')
    return len(y) / SR


def sarvam(out, text, v, pace):
    body = {'text': text, 'target_language_code': v.get('lang', 'bn-IN'), 'speaker': v['voice'],
            'model': model_for('latest-tts-sarvam', v.get('model'), 'https://api.sarvam.ai/'),
            'pace': pace, 'speech_sample_rate': int(v.get('sr', 24000))}
    if v.get('temperature') is not None: body['temperature'] = v['temperature']
    r = json.loads(_post('https://api.sarvam.ai/text-to-speech', json.dumps(body).encode(),
                         {'api-subscription-key': key('SARVAM_API_KEY', 'SHARVAM_API_KEY'), 'Content-Type': 'application/json'}))
    a = r.get('audios') or r.get('audio')
    a = a[0] if isinstance(a, list) else a
    return _to_wav(base64.b64decode(a), out)


def sarvam_clone(out, text, v, pace):
    b = uuid.uuid4().hex
    fields = {'voice_id': v['voice'], 'text': text, 'language_code': v.get('lang', 'bn-IN'), 'pace': str(pace),
              'output_audio_codec': 'wav', 'speech_sample_rate': str(SR), 'enable_vad': 'false', 'enable_qc': 'false'}
    body = b''.join(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{val}\r\n'.encode() for k, val in fields.items()) + f'--{b}--\r\n'.encode()
    r = json.loads(_post('https://api.sarvam.ai/voices/clone', body,
                         {'api-subscription-key': key('SARVAM_API_KEY', 'SHARVAM_API_KEY'), 'Content-Type': f'multipart/form-data; boundary={b}'}))
    return _to_wav(base64.b64decode(r.get('audio_b64') or r['audio']), out)


def elevenlabs(out, text, v, pace):
    body = {'text': text, 'model_id': model_for('latest-tts-elevenlabs', v.get('model'), 'https://api.elevenlabs.io/'),
            'voice_settings': {'stability': v.get('stability', 0.45), 'similarity_boost': 0.8, 'speed': max(0.7, min(1.2, pace))}}
    raw = _post(f'https://api.elevenlabs.io/v1/text-to-speech/{v["voice"]}?output_format=pcm_44100', json.dumps(body).encode(),
                {'xi-api-key': key('ELEVENLABS_API_KEY'), 'Content-Type': 'application/json'})
    return _to_wav(raw, out, sr_hint=44100)


def openai(out, text, v, pace, direction=''):
    body = {'model': model_for('latest-tts-openai', v.get('model'), 'https://api.openai.com/v1/audio/speech'),
            'voice': v.get('voice', 'alloy'), 'input': text, 'response_format': 'wav',
            'speed': max(0.25, min(4.0, pace))}
    if direction or v.get('style'): body['instructions'] = (v.get('style', '') + ' ' + direction).strip()
    raw = _post('https://api.openai.com/v1/audio/speech', json.dumps(body).encode(),
                {'Authorization': 'Bearer ' + key('OPENAI_API_KEY'), 'Content-Type': 'application/json'})
    return _to_wav(raw, out)


def placeholder(out, text, v, pace):
    cps = {'bn': 11.0, 'hi': 12.0, 'en': 14.0}.get(v.get('lang', 'en').split('-')[0], 12.0)
    d = max(1.0, len(text) / cps / max(0.5, pace)) + 0.3
    sf.write(out, np.zeros(int(d * SR), np.float32), SR, subtype='PCM_16')
    return d


PROVIDERS = {'sarvam': sarvam, 'sarvam_clone': sarvam_clone, 'elevenlabs': elevenlabs, 'openai': openai, 'placeholder': placeholder}
PAID = {'sarvam', 'sarvam_clone', 'elevenlabs', 'openai'}


BILLING = {'sarvam': ('sarvam', 'latest-tts-sarvam'), 'elevenlabs': ('elevenlabs', 'latest-tts-elevenlabs'),
           'openai': ('openai', 'latest-tts-openai')}


def plan_item(v, chars):
    """What spend.plan() needs to quote this voice for `chars` characters: provider, the model it would call, unit, units."""
    p = v.get('provider')
    if p == 'sarvam_clone':
        return {'provider': 'sarvam', 'model': 'voices/clone', 'unit': 'character', 'units': chars}
    name, alias = BILLING[p]
    prefix = {'sarvam': 'https://api.sarvam.ai/', 'elevenlabs': 'https://api.elevenlabs.io/',
              'openai': 'https://api.openai.com/v1/audio/speech'}[p]
    return {'provider': name, 'model': model_for(alias, v.get('model'), prefix), 'unit': 'character', 'units': chars}


def tts(out, text, v, pace=1.0, direction=''):
    p = v.get('provider', 'placeholder')
    if p not in PROVIDERS: raise ValueError(f'unknown provider {p}; one of {list(PROVIDERS)}')
    if p == 'openai': return openai(out, text, v, pace, direction)
    return PROVIDERS[p](out, text, v, pace)


if __name__ == '__main__':
    # quick test: python tools/voice/tts.py out.wav "text" '{"provider":"placeholder"}'
    print(tts(sys.argv[1], sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {'provider': 'placeholder'}))
