"""install_deps.py - check CutForge's Python dependencies and print the exact pinned install command.

Nothing is installed behind your back. With no flags (or --check) this reports what is present and prints the pinned pip
command for what is missing; --install runs that command for you. Every package has an exact version in PINNED (core: the versions the engine's tests ran against on
2026-10-27), so a new release reaches you only when this table changes on purpose.

    python tools/install_deps.py                      # report + print the pinned command
    python tools/install_deps.py --groups core depth  # limit the report to some groups
    python tools/install_deps.py --install            # YOU choose to run that command

Groups: core (what every tool needs), depth (depth maps and face finding), cutouts (background removal; fetches model weights
on first use), archive-search (photo search by meaning; a large download, CPU is fine). Only core is required.
Exit status: 0 nothing required is missing, 1 something required is missing, 2 a bad argument.
"""
import argparse, importlib.util, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import envcheck

# Exact versions the engine ran against. Change a pin only together with a test run.
PINNED = {
    'numpy': '2.4.4', 'soundfile': '0.14.0', 'pedalboard': '0.9.26', 'pyloudnorm': '0.2.0', 'rapidfuzz': '3.14.6',
    'opencv-python': '4.11.0.86', 'pillow': '12.3.0', 'scipy': '1.18.0',
    'onnxruntime': '1.23.2', 'rembg': '2.0.77',
    # Pinned to the newest release, but not exercised in this release's tests (archive search is optional and heavy).
    'open_clip_torch': '3.3.0', 'torch': '2.6.0',
}
IMPORT_NAMES = {'opencv-python': 'cv2', 'pillow': 'PIL', 'open_clip_torch': 'open_clip'}
GROUPS = {
    'core': ['numpy', 'soundfile', 'pedalboard', 'pyloudnorm', 'rapidfuzz', 'opencv-python', 'pillow', 'scipy'],
    'depth': ['onnxruntime'],
    'cutouts': ['rembg'],
    'archive-search': ['open_clip_torch', 'torch'],
}
REQUIRED = ['core']


def pin(package):
    if package not in PINNED:
        raise ValueError(f'no pinned version for {package!r}; add it to PINNED')
    return f'{package}=={PINNED[package]}'


def present(package):
    return importlib.util.find_spec(IMPORT_NAMES.get(package, package.replace('-', '_'))) is not None


def install_command(packages):
    return envcheck.printed_command('-m', 'pip', 'install', *(pin(p) for p in packages))


def main(argv=None):
    ap = argparse.ArgumentParser(description='Check CutForge dependencies and print the exact pinned install command.')
    ap.add_argument('--check', action='store_true', help='report only (the default)')
    ap.add_argument('--install', action='store_true', help='run the pinned pip command for what is missing')
    ap.add_argument('--groups', nargs='+', choices=sorted(GROUPS), help='groups to look at (default: core)')
    args = ap.parse_args(argv)
    groups = args.groups or REQUIRED
    notice = envcheck.python_notice()
    if notice:
        print('note:', notice, file=sys.stderr)
    missing_required, missing_any = [], []
    for g in groups:
        miss = [p for p in GROUPS[g] if not present(p)]
        print(f'  {g:15} ' + ('all present' if not miss else 'MISSING ' + ', '.join(miss)))
        missing_any += [p for p in miss if p not in missing_any]
        if g in REQUIRED:
            missing_required += miss
    if missing_any:
        cmd = install_command(missing_any)
        print('\nthe pinned command for what is missing:\n  ' + cmd)
        if args.install:
            print('\nrunning it now (you passed --install)')
            rc = subprocess.run([sys.executable, '-m', 'pip', 'install', *(pin(p) for p in missing_any)]).returncode
            return 0 if rc == 0 else 1
        print('\n(nothing was installed; add --install to run it)')
    return 1 if missing_required else 0


if __name__ == '__main__':
    sys.exit(main())
