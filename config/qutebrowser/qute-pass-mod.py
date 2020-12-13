#!/usr/bin/env nix-shell
#!nix-shell -i python3 -p "python3.withPackages(ps: [ ps.tldextract ])"

# Copyright 2017 Chris Braun (cryzed) <cryzed@googlemail.com>
#
# This file is part of qutebrowser.
#
# qutebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# qutebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with qutebrowser.  If not, see <http://www.gnu.org/licenses/>.
#
#
# HACK:
# Modified such that first search is done by path (i.e., there's a username in
# the pass path. If that fails, it looks in the secret for the username.


"""
Insert login information using pass and a dmenu-compatible application (e.g. dmenu, rofi -dmenu, ...). A short
demonstration can be seen here: https://i.imgur.com/KN3XuZP.gif.
"""

USAGE = """The domain of the site has to appear as a segment in the pass path,
for example: "github.com/cryzed" or "websites/github.com". How the username and
password are determined is freely configurable using the CLI arguments. As an
example, if you instead store the username as part of the secret (and use a
site's name as filename), instead of the default configuration, use
`--username-target secret` and `--username-pattern "username: (.+)"`.

The login information is inserted by emulating key events using qutebrowser's
fake-key command in this manner: [USERNAME]<Tab>[PASSWORD], which is compatible
with almost all login forms.

If you use gopass with multiple mounts, use the CLI switch --mode gopass to switch to gopass mode.

Suggested bindings similar to Uzbl's `formfiller` script:

    config.bind('<z><l>', 'spawn --userscript qute-pass')
    config.bind('<z><u><l>', 'spawn --userscript qute-pass --username-only')
    config.bind('<z><p><l>', 'spawn --userscript qute-pass --password-only')
    config.bind('<z><o><l>', 'spawn --userscript qute-pass --otp-only')
"""

EPILOG = """Dependencies: tldextract (Python 3 module), pass, pass-otp (optional).
For issues and feedback please use: https://github.com/cryzed/qutebrowser-userscripts.

WARNING: The login details are viewable as plaintext in qutebrowser's debug log (qute://log) and might be shared if
you decide to submit a crash report!"""

import argparse
import enum
import fnmatch
import functools
import os
import re
import shlex
import subprocess
import sys

import tldextract


def expanded_path(path):
    # Expand potential ~ in paths, since this script won't be called from a shell that does it for us
    expanded = os.path.expanduser(path)
    # Add trailing slash if not present
    return os.path.join(expanded, '')


argument_parser = argparse.ArgumentParser(description=__doc__, usage=USAGE, epilog=EPILOG)
argument_parser.add_argument('url', nargs='?', default=os.getenv('QUTE_URL'))
argument_parser.add_argument('--password-store', '-p',
                             default=expanded_path(os.getenv('PASSWORD_STORE_DIR', default='~/.password-store')),
                             help='Path to your pass password-store (only used in pass-mode)', type=expanded_path)
argument_parser.add_argument('--mode', '-M', choices=['pass', 'gopass'], default="pass",
                             help='Select mode [gopass] to use gopass instead of the standard pass.')
argument_parser.add_argument('--username-pattern', '-u', default=r'.*/(.+)',
                             help='Regular expression that matches the username')
argument_parser.add_argument('--username-target', '-U', choices=['path', 'secret'], default='path',
                             help='The target for the username regular expression')
argument_parser.add_argument('--password-pattern', '-P', default=r'Password:\s?(.+)',
                             help='Regular expression that matches the password')
argument_parser.add_argument('--dmenu-invocation', '-d', default='rofi -dmenu',
                             help='Invocation used to execute a dmenu-provider')
argument_parser.add_argument('--no-insert-mode', '-n', dest='insert_mode', action='store_false',
                             help="Don't automatically enter insert mode")
argument_parser.add_argument('--io-encoding', '-i', default='UTF-8',
                             help='Encoding used to communicate with subprocesses')
argument_parser.add_argument('--merge-candidates', '-m', action='store_true',
                             help='Merge pass candidates for fully-qualified and registered domain name')
argument_parser.add_argument('--extra-url-suffixes', '-s', default='',
                             help='Comma-separated string containing extra suffixes (e.g local)')
group = argument_parser.add_mutually_exclusive_group()
group.add_argument('--username-only', '-e', action='store_true', help='Only insert username')
group.add_argument('--password-only', '-w', action='store_true', help='Only insert password')
group.add_argument('--otp-only', '-o', action='store_true', help='Only insert OTP code')

stderr = functools.partial(print, file=sys.stderr)


class ExitCodes(enum.IntEnum):
    SUCCESS = 0
    FAILURE = 1
    # 1 is automatically used if Python throws an exception
    NO_PASS_CANDIDATES = 2
    COULD_NOT_MATCH_USERNAME = 3
    COULD_NOT_MATCH_PASSWORD = 4


def qute_command(command):
    with open(os.environ['QUTE_FIFO'], 'w') as fifo:
        fifo.write(command + '\n')
        fifo.flush()


def find_pass_candidates(domain):
    candidates = []

    if arguments.mode == "gopass":
        all_passwords = subprocess.run(["gopass", "list", "--flat" ], stdout=subprocess.PIPE).stdout.decode("UTF-8").splitlines()

        for password in all_passwords:
            if domain in password:
                candidates.append(password)
    else:
        for path, directories, file_names in os.walk(arguments.password_store, followlinks=True):
            secrets = fnmatch.filter(file_names, '*.gpg')
            if not secrets:
                continue

            # Strip password store path prefix to get the relative pass path
            pass_path = path[len(arguments.password_store):]
            split_path = pass_path.split(os.path.sep)
            for secret in secrets:
                secret_base = os.path.splitext(secret)[0]
                if domain not in (split_path + [secret_base]):
                    continue

                candidates.append(os.path.join(pass_path, secret_base))
    return candidates


def _run_pass(pass_arguments):
    # The executable is conveniently named after it's mode [pass|gopass].
    pass_command = [arguments.mode]
    env = os.environ.copy()
    env['PASSWORD_STORE_DIR'] = arguments.password_store
    process = subprocess.run(pass_command + pass_arguments, env=env, stdout=subprocess.PIPE)
    return process.stdout.decode(arguments.io_encoding).strip()


def pass_(path):
    return _run_pass(['show', path])


def pass_otp(path):
    return _run_pass(['otp', path])


def dmenu(items, invocation):
    command = shlex.split(invocation)
    process = subprocess.run(command, input='\n'.join(items).encode(arguments.io_encoding), stdout=subprocess.PIPE)
    return process.stdout.decode(arguments.io_encoding).strip()


def fake_key_raw(text):
    for character in text:
        # Escape all characters by default, space requires special handling
        sequence = '" "' if character == ' ' else '\{}'.format(character)
        qute_command('fake-key {}'.format(sequence))


def main(arguments):
    if not arguments.url:
        argument_parser.print_help()
        return ExitCodes.FAILURE

    extractor = tldextract.TLDExtract(extra_suffixes=arguments.extra_url_suffixes.split(','))
    extract_result = extractor(arguments.url)

    # Try to find candidates using targets in the following order: fully-qualified domain name (includes subdomains),
    # the registered domain name, the IPv4 address if that's what the URL represents and finally the private domain
    # (if a non-public suffix was used).
    candidates = set()
    attempted_targets = []

    private_domain = ''
    if not extract_result.suffix:
        private_domain = ('.'.join((extract_result.subdomain, extract_result.domain))
                          if extract_result.subdomain else extract_result.domain)

    for target in filter(None, [extract_result.fqdn, extract_result.registered_domain, extract_result.ipv4, private_domain]):
        attempted_targets.append(target)
        target_candidates = find_pass_candidates(target)
        if not target_candidates:
            continue

        candidates.update(target_candidates)
        if not arguments.merge_candidates:
            break
    else:
        if not candidates:
            stderr('No pass candidates for URL {!r} found! (I tried {!r})'.format(arguments.url, attempted_targets))
            return ExitCodes.NO_PASS_CANDIDATES

    selection = candidates.pop() if len(candidates) == 1 else dmenu(sorted(candidates), arguments.dmenu_invocation)
    # Nothing was selected, simply return
    if not selection:
        return ExitCodes.SUCCESS

    secret = pass_(selection)

    # Match password
    match = re.match(arguments.password_pattern, secret)
    if not match:
        # ok, forget the pattern, try getting anything
        match = re.match(r'(.*)', secret)
        if not match:
            stderr('Failed to match password pattern on secret!')
            return ExitCodes.COULD_NOT_MATCH_PASSWORD
    password = match.group(1)

    # Match username
    target = selection if arguments.username_target == 'path' else secret
    match = re.search(arguments.username_pattern, target, re.MULTILINE)
    if not match:
        stderr('Failed to match username pattern on {}! Will try matching in secret..'.format(arguments.username_target))
        match = re.search(r'.*^[u|U]sername:\s?(.+)', secret , re.MULTILINE)
        if not match:
            return ExitCodes.COULD_NOT_MATCH_USERNAME
    username = match.group(1)

    if arguments.username_only:
        fake_key_raw(username)
        qute_command('fake-key <Tab>')
    elif arguments.password_only:
        fake_key_raw(password)
        qute_command('fake-key <Tab>')
    elif arguments.otp_only:
        otp = pass_otp(selection)
        fake_key_raw(otp)
        qute_command('fake-key <Tab>')
    else:
        # Enter username and password using fake-key and <Tab> (which seems to work almost universally), then switch
        # back into insert-mode, so the form can be directly submitted by hitting enter afterwards
        fake_key_raw(username)
        qute_command('fake-key <Tab>')
        fake_key_raw(password)
        qute_command('fake-key <Tab>')

    if arguments.insert_mode:
        qute_command('enter-mode insert')

    return ExitCodes.SUCCESS


if __name__ == '__main__':
    arguments = argument_parser.parse_args()
    sys.exit(main(arguments))
