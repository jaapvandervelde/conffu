from logging import warning, error
from os import chdir
from sys import argv
from pathlib import Path
from subprocess import run
import re


def change_dir():
    root = Path(__file__).absolute().parent
    chdir(root / '..')
    return True


def check_file(name, critical=True, msg=''):
    if Path(name).is_file():
        return True
    else:
        if not critical:
            warning(f'Non-critical file {name} missing' if not msg else msg)
        else:
            error(f'Critical file {name} missing' if not msg else msg)


def get_package_name():
    with open('setup.py') as f:
        setup = f.read()
    return re.search(r"__name__\s*=\s*'(.+?)'", setup, re.DOTALL).group(1)


def check_critical_files(package_name):
    return (
        check_file('setup.cfg') and
        check_file('setup.py') and
        check_file('LICENSE') and
        check_file('CHANGELOG.md') and
        check_file('.gitignore') and
        check_file('setup.cfg') and
        check_file(f'{package_name}/_version.py') and
        check_file(f'{package_name}/__init__.py')
    )


def check_version(package_name, arg_version):
    import importlib.util
    spec = importlib.util.spec_from_file_location("_version", f"{package_name}/_version.py")
    _version = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_version)
    # noinspection PyUnresolvedReferences
    v = _version.__version__

    result = True
    from packaging import version

    if arg_version is not None and v != arg_version:
        error(f'Version in _version.py {v} does not match specified version {arg_version}')
        result = False

    with open('CHANGELOG.md', 'r') as f:
        changelog = f.read()

    version_in_changelog = any(
        (match == v) if match else False
        for match in re.findall('\#\# \[([\d.]+?\w*)\] - \d{4}-\d{2}-\d{2}', changelog)
    )
    if not version_in_changelog:
        error(f'There is no expected entry ## [{v}] - <ISO date> in CHANGELOG.md')
        result = False

    for match in re.findall('\#\# \[([\d.]+?\w*)\] - \d{4}-\d{2}-\d{2}', changelog):
        if version.parse(match) > version.parse(v):
            error(f'There is a later entry than {v}, namely {match} in CHANGELOG.md, check _version.py')
            result = False

    version_in_changelog = any(
        (match[1] == match[0] == v) if match else False
        for match in re.findall('\[([\d.]+\w*)\]: /\.\./\.\./\.\./tags/([\d.]+\w*)', changelog)
    )
    if not version_in_changelog:
        error(f'There is no expected reference [{v}]: /../../../tags/{v} in CHANGELOG.md')
        result = False

    # check if last tag either matches v, or is the next minor version
    git_tag = run('git describe --tags --abbrev=0', capture_output=True).stdout.decode().strip()
    if version.parse(v) < version.parse(git_tag):
        warning(f'Latest git tag "{git_tag}" does not match or precede version number "{v}"')

    return result


def main():
    change_dir()

    package_name = get_package_name()
    arg_version = None if len(argv) != 2 else argv[1]

    ok = (
        check_critical_files(package_name) and
        check_version(package_name, arg_version)
    )
    if not ok:
        exit(1)


if __name__ == '__main__':
    main()