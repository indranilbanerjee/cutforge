"""The spend gate: a live quote, a provider list the client approved, a typed go and a cap, checked in that order.
Every paid call goes through plan() before it runs and log_plan() after it. Nothing here knows a price: they come from
price_book.py, recorded from the provider's own page.

The flow a skill follows:
  1. run the paid tool WITHOUT --go: it prints the quote (provider, model, units, amount, where the price was read) and exits 4;
     nothing is spent;
  2. show the client that quote and wait for their typed go;
  3. run the same command with  --go --quoted-providers <the providers in the quote>.
A provider that is not in --quoted-providers never runs (NeedsRequote), a price that is missing or stale blocks the run
(NeedsQuote), and the cap (config.json budget_inr, budget_usd ...) is checked against spend.md before every run.
A file in the project cannot stand in for the client's go: GO_AHEAD.txt is no longer read, because an agent can create it.

usage in code:  from spend import plan, log_plan, parse_flags, plan_or_exit
usage on CLI :  python tools/spend.py            (prints the totals and the caps)
Exit status of the paid tools: 4 = a quote, a requote or a go is needed (nothing was spent)."""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import cli; cli.guard(__name__, __file__, __doc__)
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROOT, CFG
import price_book

LOG = os.path.join(ROOT, 'spend.md')
HEADER = '# Spend log (one line per paid call)\n\n| time | tool | provider | model | for | amount | currency | note |\n|---|---|---|---|---|---|---|---|\n'
EXIT_NEEDS_ACTION = 4


class NeedsQuote(PermissionError):
    """A fresh price is missing: look it up and record it."""


class NeedsRequote(PermissionError):
    """A provider is not in the approved quote: show a new quote."""


class NeedsGo(PermissionError):
    """The quote was produced but the client has not said go."""


def total(currency='INR'):
    """Spent so far in `currency`, from spend.md (older rows written as '₹12.00' count as INR)."""
    if not os.path.exists(LOG):
        return 0.0
    s = 0.0
    with open(LOG, encoding='utf-8-sig') as f:
        for line in f:
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if len(cells) == 8 and cells[6].upper() == currency.upper():
                try: s += float(cells[5])
                except ValueError: pass
            elif len(cells) == 7 and cells[5] == 'total' and cells[4].startswith('₹') and currency.upper() == 'INR':
                try: s += float(cells[4][1:])
                except ValueError: pass
    return round(s, 2)


def cap(currency):
    value = CFG.get('budget_' + currency.lower())
    return float(value) if value is not None else None


def parse_flags(argv):
    """(go, quoted providers, remaining argv): pulls --go and --quoted-providers a,b out of a command line."""
    rest, go, quoted, i = [], False, [], 0
    while i < len(argv):
        a = argv[i]
        if a == '--go': go = True
        elif a == '--quoted-providers' and i + 1 < len(argv):
            i += 1; quoted = [p.strip().lower() for p in argv[i].split(',') if p.strip()]
        elif a.startswith('--quoted-providers='):
            quoted = [p.strip().lower() for p in a.split('=', 1)[1].split(',') if p.strip()]
        else: rest.append(a)
        i += 1
    return go, quoted, rest


def describe(quotes):
    lines = [f"  {q['provider']} / {q['model']}: about {q['amount']:.2f} {q['currency']} for {q['units']:g} {q['unit']} "
             f"(price {q['price']:g} {q['currency']} per {q['price_unit']}, read {q['read_on'][:10]} at {q['source']})" for q in quotes]
    return '\n'.join(lines)


def plan(tool, items, quoted=None, go=False):
    """Check a paid operation before it runs. items: [{'provider', 'model', 'unit', 'units'}]. Returns {'items', 'totals'} when the
    run may go ahead; raises NeedsQuote, NeedsRequote, NeedsGo or PermissionError (the cap) with the next step in the message."""
    quotes = [price_book.quote(i['provider'], i['model'], i['units'], i.get('unit', 'request')) for i in items]
    bad = [q for q in quotes if q['status'] != 'ok']
    if bad:
        raise NeedsQuote(f'{tool}: no fresh price, so nothing was spent. ' + ' | '.join(f"{q['status']}: {q['look_up']}" for q in bad))
    providers = sorted({i['provider'].lower() for i in items})
    totals = {}
    for q in quotes:
        totals[q['currency']] = round(totals.get(q['currency'], 0.0) + q['amount'], 4)
    summary = f'{tool} would cost ' + ' + '.join(f'{v:.2f} {c}' for c, v in totals.items()) + ':\n' + describe(quotes)
    flags = f'--go --quoted-providers {",".join(providers)}'
    if not go:
        raise NeedsGo(summary + f'\nNothing was spent. Show this to the client; after their typed go, run the same command with {flags}')
    covered = [p.lower() for p in (quoted or [])]
    outside = [p for p in providers if p not in covered]
    if outside:
        raise NeedsRequote(summary + f'\nNothing was spent: {", ".join(outside)} is not in --quoted-providers. '
                           f'Show the client this quote and run with {flags} only after their go.')
    for ccy, amount in totals.items():
        limit = cap(ccy)
        if limit is None and ccy.upper() not in ('INR',) and cap('INR') is not None:
            raise PermissionError(f'{tool}: the quote is in {ccy} but the cap is in INR; add budget_{ccy.lower()} to config.json '
                                  'or record the price in INR. Nothing was spent.')
        if limit is not None and total(ccy) + amount > limit:
            raise PermissionError(f'{tool}: would pass the budget cap (spent {total(ccy)} {ccy}, this about {amount:.2f}, cap {limit:g}). '
                                  'Stop and tell the client.')
    return {'items': quotes, 'totals': totals, 'summary': summary}


def plan_or_exit(tool, items, go, quoted):
    """plan() for a command line: print the quote or the reason and exit 4 instead of raising."""
    try:
        return plan(tool, items, quoted=quoted, go=go)
    except (NeedsQuote, NeedsRequote, NeedsGo, PermissionError) as e:
        print(e, file=sys.stderr if not isinstance(e, NeedsGo) else sys.stdout)
        sys.exit(EXIT_NEEDS_ACTION)


def log_plan(tool, the_plan, purpose, note=''):
    new = not os.path.exists(LOG)
    with open(LOG, 'a', encoding='utf-8') as f:
        if new: f.write(HEADER)
        for q in the_plan['items']:
            f.write(f"| {time.strftime('%Y-%m-%d %H:%M')} | {tool} | {q['provider']} | {q['model']} | {purpose} | {q['amount']:.2f} | {q['currency']} | {note} |\n")
    return {c: total(c) for c in the_plan['totals']}


if __name__ == '__main__':
    print('spent so far:', {c: total(c) for c in ('INR', 'USD')},
          '| caps:', {c: cap(c) for c in ('INR', 'USD')}, '| prices recorded:', len(price_book.load()))
