"""resolve_model.py - which model a CutForge tool should call, from tools/model_registry.json and never from a literal.

The registry is a copy of the suite's canonical one (a sync from Digital Marketing Pro writes it), so the speech models,
their shutdown dates and their pin expiry arrive together. A tool names a capability, `latest-tts-sarvam`, and gets the model id,
the endpoint the registry says serves it, and any warning, instead of carrying a model id in its own code.

    python tools/resolve_model.py --alias latest-stt-sarvam
    python tools/resolve_model.py --check <model id>
    python tools/resolve_model.py --aliases

Python:
    from resolve_model import resolve_for_execution, ModelError
    r = resolve_for_execution('latest-stt-sarvam', endpoint_prefix='https://api.sarvam.ai/')   # {'model': '<the registry's id>', ...}

What it refuses (ModelError, CLI exit 3), rather than guessing:
  * an alias or id the registry does not know;
  * a retired model, or one whose shutdown date has passed;
  * a pinned (speech) model whose pin has expired: the registry must be re-read and re-synced first. Set
    CUTFORGE_ALLOW_EXPIRED_PINS=1 to run on a stale pin knowingly; the result then carries a warning;
  * a model served at a different endpoint than the tool can call (OpenAI's text-to-speech replacement is Realtime-only).
It warns (never blocks) for a deprecated model, a shutdown within 60 days, and a registry not reviewed for over 60 days.

Exit status: 0 resolved or listed, 1 --check found a deprecated, retired or unknown id, 2 the registry is missing or unreadable,
3 a refusal above.
"""
import argparse, json, os, sys
from datetime import date

REGISTRY = os.environ.get('CUTFORGE_MODEL_REGISTRY') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model_registry.json')
STALE_REGISTRY_DAYS = 60
SHUTDOWN_WARN_DAYS = 60


class ModelError(Exception):
    pass


def today():
    frozen = os.environ.get('CUTFORGE_TODAY')          # tests freeze the day
    return date.fromisoformat(frozen) if frozen else date.today()


def load():
    try:
        with open(REGISTRY, encoding='utf-8-sig') as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        raise ModelError(f'cannot read the model registry {REGISTRY}: {e}') from None


def _d(value):
    return date.fromisoformat(value[:10]) if value else None


def replacement_text(m):
    """What the registry names as a model's replacement. An entry whose replacement depends on the service a request goes to
    (replacement_by_backend) names every one with its service, never a single id that only one service serves."""
    by_backend = m.get('replacement_by_backend') or {}
    if by_backend:
        return ' or '.join(f'{rep} ({name})' for name, rep in sorted(by_backend.items()))
    return m.get('replacement_id')


def resolve_for_execution(alias_or_id, endpoint_prefix=None, allow_expired=None):
    """The model to call for `alias_or_id`, with provenance and warnings, or a ModelError that says what to do."""
    reg = load()
    models = {m['id']: m for m in reg.get('models', [])}
    model_id = reg.get('aliases', {}).get(alias_or_id, alias_or_id)
    m = models.get(model_id)
    if m is None:
        raise ModelError(f'{alias_or_id!r} is neither an alias nor a model in the registry ({REGISTRY}). '
                         'Run: python tools/resolve_model.py --aliases, or ask for a registry sync.')
    now, warnings = today(), []
    status = m.get('status', 'current')
    shutdown = _d(m.get('shutdown_date'))
    if status == 'retired' or (shutdown and shutdown <= now):
        raise ModelError(f'{model_id} is retired (shut down {shutdown or "already"}); use {replacement_text(m) or "a current model"}')
    if status == 'deprecated' or shutdown:
        when = f' and shuts down {shutdown}' if shutdown else ''
        warnings.append(f'{model_id} is {status}{when}; the registry names {replacement_text(m) or "no replacement"}')
        if shutdown and (shutdown - now).days <= SHUTDOWN_WARN_DAYS:
            warnings.append(f'{model_id} shuts down in {(shutdown - now).days} days')
    expires = _d(m.get('pin_expires'))
    if expires and expires < now:
        if allow_expired is None:
            allow_expired = os.environ.get('CUTFORGE_ALLOW_EXPIRED_PINS') == '1'
        message = (f'the pin on {model_id} expired {expires}: vendors change speech models without notice, so re-read '
                   f'{m.get("docs_url", "the vendor page")} and sync the registry before spending')
        if not allow_expired:
            raise ModelError(message + ' (CUTFORGE_ALLOW_EXPIRED_PINS=1 runs on it knowingly)')
        warnings.append(message)
    endpoint = m.get('api_endpoint', '')
    if endpoint_prefix and not endpoint.startswith(endpoint_prefix):
        raise ModelError(f'{model_id} is served at {endpoint or "an endpoint the registry does not give"}, not at {endpoint_prefix}: '
                         'this tool cannot call it. ' + (m.get('notes', '') or '')[:240])
    updated = _d(reg.get('last_updated'))
    if updated and (now - updated).days > STALE_REGISTRY_DAYS:
        warnings.append(f'the registry was last reviewed {updated} ({(now - updated).days} days ago)')
    return {'alias': alias_or_id if alias_or_id != model_id else None, 'model': model_id, 'vendor': m.get('vendor'),
            'status': status, 'api_endpoint': endpoint, 'docs_url': m.get('docs_url'), 'pin_expires': m.get('pin_expires'),
            'registry_last_updated': reg.get('last_updated'), 'warnings': warnings}


def model_for(alias, explicit=None, endpoint_prefix=None):
    """The id a tool sends: the user's own `model` setting when given (still checked, so a deprecated or shut-down one is
    reported), else the registry's choice for the capability alias."""
    result = resolve_for_execution(explicit or alias, endpoint_prefix=endpoint_prefix)
    for w in result['warnings']:
        print('model note:', w, file=sys.stderr)
    return result['model']


def main(argv=None):
    ap = argparse.ArgumentParser(description='Resolve a CutForge capability alias to a model id from the registry.')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--alias', help='a capability alias such as latest-tts-sarvam')
    g.add_argument('--check', metavar='ID', help='status of one model id')
    g.add_argument('--aliases', action='store_true', help='list every alias and what it resolves to')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    try:
        if args.aliases:
            reg = load()
            for k, v in sorted(reg.get('aliases', {}).items()):
                print(f'{k:36} {v}')
            return 0
        if args.alias:
            r = resolve_for_execution(args.alias)
            print(json.dumps(r, indent=2) if args.json else f"{r['model']}" + ''.join(f"\n  note: {w}" for w in r['warnings']))
            return 0
        reg = load()
        m = next((x for x in reg.get('models', []) if x['id'] == args.check), None)
        if m is None:
            print(f'{args.check}: unknown'); return 1
        status = m.get('status', 'current')
        print(f'{args.check}: {status}' + (f' (use {replacement_text(m)})' if replacement_text(m) else ''))
        return 0 if status in ('current', 'supported') else 1
    except ModelError as e:
        print(f'resolve_model.py: {e}', file=sys.stderr)
        return 2 if 'cannot read the model registry' in str(e) else 3


if __name__ == '__main__':
    sys.exit(main())
