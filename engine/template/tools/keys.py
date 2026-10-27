"""API keys: environment variable first, then the key file named in config.json (api_keys_file).
The file holds one NAME=value (or NAME: value) per line. Keys are returned, never printed or logged.
usage: from keys import key; key('SARVAM_API_KEY')      check: python tools/keys.py NAME [NAME...]"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import cli; cli.guard(__name__, __file__, __doc__)
import os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import CFG


def keyed_request(url, headers, data=None):
    """A urllib Request that sends `headers` (the key among them) to `url` and to no other host. urllib copies a request's ordinary
    headers to whatever host a 30x answer names; add_unredirected_header keeps them on this first request only."""
    req = urllib.request.Request(url, data=data)
    for name, value in headers.items(): req.add_unredirected_header(name, value)
    return req


def key(name, *aliases):
    for n in (name,) + aliases:
        if os.environ.get(n):
            return os.environ[n].strip()
    f = CFG.get('api_keys_file')
    if f and os.path.exists(f):
        for line in open(f, encoding='utf-8-sig', errors='ignore'):
            s = line.strip()
            for n in (name,) + aliases:
                if s.startswith(n) and re.match(rf'^{re.escape(n)}\s*[=:]', s):
                    return re.split(r'[=:]\s*', s, 1)[1].strip().strip('"\'')
    raise KeyError(f'{name}: not in the environment or in config.api_keys_file')


if __name__ == '__main__':
    for n in sys.argv[1:]:
        try:
            v = key(n); print(f'{n}: found ({len(v)} chars)')
        except KeyError as e:
            print(e)
