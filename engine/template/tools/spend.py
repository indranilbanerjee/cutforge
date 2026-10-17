"""The budget gate. Every paid call goes through gate() before it runs and log() after it.
- No GO_AHEAD.txt in the project root -> refuse (the client has not approved spending yet).
- Estimated running total past config.budget_inr -> refuse and say so.
- Every call is one line in spend.md: time, tool, model, what for, estimated cost, running total.
usage in code:  from spend import gate, log;  gate('wavespeed', 40);  ...call...;  log('wavespeed', 'kling-v3', 'road shot', 40)
usage on CLI :  python tools/spend.py            (prints the total and the cap)"""
import os, sys, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import ROOT, CFG

LOG = os.path.join(ROOT, 'spend.md')
GO = os.path.join(ROOT, 'GO_AHEAD.txt')


def total():
    if not os.path.exists(LOG): return 0.0
    s = 0.0
    for line in open(LOG, encoding='utf-8'):
        m = re.search(r'\|\s*₹?\s*([0-9.]+)\s*\|\s*total', line)
        if m: s += float(m.group(1))
    return round(s, 2)


def gate(tool, est_inr):
    if not os.path.exists(GO):
        raise PermissionError(f'{tool}: paid call blocked. The client has not said go ahead (create GO_AHEAD.txt only after they do).')
    cap = CFG.get('budget_inr')
    if cap is not None and total() + est_inr > float(cap):
        raise PermissionError(f'{tool}: would pass the budget cap (spent ₹{total()}, this ≈₹{est_inr}, cap ₹{cap}). Stop and tell the client.')


def log(tool, model, purpose, inr, note=''):
    new = not os.path.exists(LOG)
    with open(LOG, 'a', encoding='utf-8') as f:
        if new: f.write('# Spend log (one line per paid call)\n\n| time | tool | model | for | ₹ | total | note |\n|---|---|---|---|---|---|---|\n')
        f.write(f"| {time.strftime('%Y-%m-%d %H:%M')} | {tool} | {model} | {purpose} | ₹{inr:.2f} | total | {note} |\n")
    return total()


if __name__ == '__main__':
    print(f'spent ≈₹{total()} of cap ₹{CFG.get("budget_inr", "unset")}; go-ahead file: {"yes" if os.path.exists(GO) else "no"}')
