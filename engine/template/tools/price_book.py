"""price_book.py - what a paid call costs, from a price somebody read on the provider's page, never from memory.

This module holds no prices. A price enters only through `record`, which requires the https page it was read from, and it
expires (168 hours by default, config.json "price_max_age_hours"). `quote` answers with a status, never a bare number: a missing
or stale price says what to look up, and the tools refuse to spend until it is recorded. There is no seed table and no "typical
rate" fallback, because a rate typed into code is wrong the day a provider changes it.

Prices live in price_book.json in the project root. The agent reads the provider's pricing page with its own web tools and
records what it read:

    python tools/price_book.py record --provider <provider> --model <model id> --unit 1k-characters --price <price> \\
        --currency <ISO code> --source <the provider's https pricing page>
    python tools/price_book.py quote  --provider <provider> --model <model id> --units 12000 --unit character
    python tools/price_book.py show

Units convert inside a family: character / 1k-characters / 1m-characters, second / minute / hour. Anything else (image, clip,
request) must be asked for in the unit it was recorded in.
Exit status: 0 done, 4 a fresh price is needed (nothing was spent), 2 a bad argument.
"""
import argparse, json, os, sys, time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROOT, CFG

BOOK = os.path.join(ROOT, 'price_book.json')
FAMILIES = {
    'text': {'character': 1, '1k-characters': 1000, '1m-characters': 1000000},
    'time': {'second': 1, 'minute': 60, 'hour': 3600},
}


def _family(unit):
    for name, units in FAMILIES.items():
        if unit in units:
            return name
    return unit            # image, clip, request ...: its own family of one


def _factor(unit):
    return FAMILIES.get(_family(unit), {}).get(unit, 1)


def _now():
    frozen = os.environ.get('CUTFORGE_NOW')            # tests freeze the clock
    return datetime.fromisoformat(frozen) if frozen else datetime.now(timezone.utc)


def _key(provider, model):
    return f'{provider.strip().lower()}|{model.strip().lower()}'


def load():
    try:
        with open(BOOK, encoding='utf-8-sig') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def record(provider, model, unit, price, currency, source):
    if not str(source).startswith('https://'):
        raise ValueError('a price needs the https page it was read from (--source)')
    if float(price) < 0:
        raise ValueError('a price cannot be negative')
    book = load()
    book[_key(provider, model)] = {'provider': provider, 'model': model, 'unit': unit, 'price': float(price),
                                   'currency': currency.upper(), 'source': source, 'read_on': _now().isoformat(timespec='seconds')}
    with open(BOOK, 'w', encoding='utf-8') as f:
        json.dump(book, f, ensure_ascii=False, indent=1)
    return book[_key(provider, model)]


def max_age_hours():
    return float(CFG.get('price_max_age_hours', 168))


def quote(provider, model, units, unit='request'):
    """{'status': 'ok'|'missing'|'stale', ...}. 'ok' carries amount, currency, price, unit, source, read_on and age_hours."""
    entry = load().get(_key(provider, model))
    look = (f'read the price for {provider} / {model} on the provider\'s pricing page, then: python tools/price_book.py record '
            f'--provider {provider} --model "{model}" --unit <unit> --price <price> --currency <ISO code> --source <https page>')
    if not entry:
        return {'status': 'missing', 'provider': provider, 'model': model, 'look_up': look}
    if _family(entry['unit']) != _family(unit):
        return {'status': 'missing', 'provider': provider, 'model': model,
                'look_up': f'the recorded price is per {entry["unit"]} and this call is counted in {unit}; ' + look}
    read_on = datetime.fromisoformat(entry['read_on'])
    age = (_now() - (read_on if read_on.tzinfo else read_on.replace(tzinfo=timezone.utc))).total_seconds() / 3600
    if age > max_age_hours():
        return {'status': 'stale', 'provider': provider, 'model': model, 'age_hours': round(age, 1), 'look_up': look}
    amount = entry['price'] / _factor(entry['unit']) * units * _factor(unit)
    return {'status': 'ok', 'provider': provider, 'model': model, 'units': units, 'unit': unit, 'amount': round(amount, 4),
            'currency': entry['currency'], 'price': entry['price'], 'price_unit': entry['unit'], 'source': entry['source'],
            'read_on': entry['read_on'], 'age_hours': round(age, 1)}


def main(argv=None):
    ap = argparse.ArgumentParser(description='Record and quote paid-call prices (no prices ship with the plugin).')
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('record'); r.add_argument('--provider', required=True); r.add_argument('--model', required=True)
    r.add_argument('--unit', required=True); r.add_argument('--price', type=float, required=True)
    r.add_argument('--currency', required=True); r.add_argument('--source', required=True)
    q = sub.add_parser('quote'); q.add_argument('--provider', required=True); q.add_argument('--model', required=True)
    q.add_argument('--units', type=float, required=True); q.add_argument('--unit', default='request')
    sub.add_parser('show')
    args = ap.parse_args(argv)
    if args.cmd == 'record':
        try:
            print(json.dumps(record(args.provider, args.model, args.unit, args.price, args.currency, args.source), indent=1))
        except ValueError as e:
            print(f'price_book.py: {e}', file=sys.stderr); return 2
        return 0
    if args.cmd == 'quote':
        out = quote(args.provider, args.model, args.units, args.unit)
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0 if out['status'] == 'ok' else 4
    for k, e in sorted(load().items()):
        print(f"{k:40} {e['price']} {e['currency']} per {e['unit']}  read {e['read_on'][:16]}  {e['source']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
