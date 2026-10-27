"""cli.py - -h/--help and unknown options for every engine tool, decided before the tool does anything.

A tool's first two lines after its docstring are
    import cli; cli.guard(__name__, __file__, __doc__)
and the guard does three things only when the file is run as a command (it does nothing when the file is imported):
  * -h or --help prints the tool's docstring (its usage) and exits 0, having run nothing: no file written, no model fetched,
    no network call. Before 1.1.1 `--help` RAN most tools: synth.py wrote sound files, cutout.py started a model download,
    film_mix.py re-mixed, and the rest crashed treating "--help" as a path.
  * an option starting with -- that the tool does not know exits 2 with a one-line message, spending and writing nothing.
    A tool's options are the --flags its own source (and its docstring) mention; the paid tools pass `extra=` for the two flags
    spend.parse_flags reads (--go and --quoted-providers).
  * a command that cannot start because of its arguments exits 2 (the suite's convention for a bad argument).
Tools that use argparse (install_deps.py, price_book.py, resolve_model.py) already do all of this and do not use the guard.
Stdlib only.
"""
import os, re, sys

SPEND_FLAGS = ('--go', '--quoted-providers')
FLAG = re.compile(r"""['"`\s\[(|](--[a-z][a-z0-9-]*)""")


def known_options(file, doc, extra=()):
    try:
        with open(file, encoding='utf-8-sig') as f:
            source = f.read()
    except OSError:
        source = ''
    return set(FLAG.findall(source)) | set(FLAG.findall(' ' + (doc or ''))) | set(extra) | {'--help'}


def guard(name, file, doc, extra=()):
    """Call first in a tool, as `import cli; cli.guard(__name__, __file__, __doc__)`."""
    if name != '__main__':
        return
    args = sys.argv[1:]
    if any(a in ('-h', '--help') for a in args):
        print((doc or f'{os.path.basename(file)}: no usage text').strip())
        sys.exit(0)
    known = known_options(file, doc, extra)
    unknown = [a.split('=', 1)[0] for a in args if a.startswith('--') and a.split('=', 1)[0] not in known]
    if unknown:
        print(f'{os.path.basename(file)}: unknown option {unknown[0]}; run it with --help for the usage', file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    guard(__name__, __file__, __doc__)
