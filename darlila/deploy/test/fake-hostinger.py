#!/usr/bin/env python3
"""
============================================================
 SERVEUR HOSTINGER SIMULÉ — pour tester `npm run deploy`
============================================================
Reproduit le strict nécessaire d'un hébergement mutualisé
Hostinger, sans compte réel :

  • SSH avec authentification par mot de passe (port 2222)
  • SFTP mappé sur ./server-root (les fichiers téléversés
    par le script de déploiement y apparaissent réellement)
  • Canal « exec » qui simule composer / php artisan
    (réponses réalistes, codes retour 0)

Identifiants de test :  u123456789 / test123

Utilisation :
    python3 fake-hostinger.py            (puis, ailleurs :)
    cd .. && npm run deploy -- --config test/deploy.test.config.json

Après le déploiement, inspecter :
    ls test/server-root/home/u123456789/domains/
============================================================
"""
import os
import posixpath
import socket
import threading

import paramiko
from paramiko import (
    AUTH_FAILED,
    AUTH_SUCCESSFUL,
    OPEN_SUCCEEDED,
    SFTPAttributes,
    SFTPHandle,
    SFTPServerInterface,
    ServerInterface,
)
from paramiko.sftp import SFTP_NO_SUCH_FILE, SFTP_OK

HOST = '127.0.0.1'
PORT = 2222
USERNAME = 'u123456789'
PASSWORD = 'test123'
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server-root')

# ------------------------------------------------------------------ #
# Simulation des commandes serveur (composer, php artisan…)           #
# ------------------------------------------------------------------ #


def simulate_command(command: str) -> str:
    """Réponses réalistes des commandes exécutées par deploy.mjs."""
    if 'command -v' in command:
        return '/usr/local/bin/composer\n'

    if 'composer install' in command:
        return (
            'Installing dependencies from lock file (including require-dev)\n'
            'Package operations: 0 installs, 0 updates, 0 removals\n'
            'Generating optimized autoload files\n'
            '[Simulé — serveur de test]\n'
        )

    if 'key:generate' in command:
        return 'INFO  Application key set successfully.\n'

    if 'migrate' in command:
        lines = [
            'INFO  Preparing database.',
            '  Creating migration table ......................... DONE',
            '  0001_01_01_000000_create_users_table ............ DONE',
            '  2026_08_26_000001_create_categories_table ........ DONE',
            '  2026_08_26_000002_create_products_table .......... DONE',
            '  2026_08_26_000003_create_reviews_table .......... DONE',
            '  2026_08_26_000004_create_orders_table ........... DONE',
            '  2026_08_26_000005_create_order_items_table ...... DONE',
            '  2026_08_26_000006_create_gallery_images_table ... DONE',
            '  2026_08_26_000007_create_settings_table ......... DONE',
            '  2026_08_26_000008_create_users_table ............ DONE',
            '  2026_08_26_000009_create_personal_access_tokens . DONE',
            'INFO  Seeding database.',
            '  Database\\Seeders\\CategorySeeder .................. RUNNING',
            '  Database\\Seeders\\ProductSeeder ................... RUNNING',
            '  Database\\Seeders\\ReviewSeeder .................... RUNNING',
            '  Database\\Seeders\\GallerySeeder ................... RUNNING',
            '  Database\\Seeders\\SettingSeeder ................... RUNNING',
            '  Database\\Seeders\\UserSeeder ...................... RUNNING',
            'INFO  1002 produits, 8 catégories, compte admin créé.',
            '[Simulé — serveur de test]',
        ]
        return '\n'.join(lines) + '\n'

    if 'storage:link' in command:
        return 'INFO  The [public_html/storage] directory has been linked.\n'

    if 'optimize' in command:
        return (
            'INFO  Configuration cached successfully.\n'
            'INFO  Routes cached successfully.\n'
            'INFO  Views cached successfully.\n'
            'INFO  Event listeners cached successfully.\n'
        )

    if command.strip():
        return '[simulé] ' + command.strip()[:120] + '\n'
    return ''


# ------------------------------------------------------------------ #
# Interface SSH (auth + canaux)                                       #
# ------------------------------------------------------------------ #


class FakeHostinger(ServerInterface):
    def check_auth_password(self, username, password):
        if username == USERNAME and password == PASSWORD:
            return AUTH_SUCCESSFUL
        print(f'  [ssh] auth refusée pour « {username} »')
        return AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'password'

    def check_channel_request(self, kind, chanid):
        return OPEN_SUCCEEDED

    def check_channel_exec_request(self, channel, command):
        command = command.decode('utf-8', errors='replace')
        print(f'  [exec] {command[:100]}{"…" if len(command) > 100 else ""}')

        def run():
            try:
                import time

                time.sleep(0.05)
                output = simulate_command(command)
                if output:
                    channel.sendall(output.encode('utf-8'))
                channel.send_exit_status(0)
                channel.close()
            except Exception as error:  # pragma: no cover
                print('  [exec] erreur :', error)

        threading.Thread(target=run, daemon=True).start()
        return True


# ------------------------------------------------------------------ #
# Interface SFTP (mappée sur server-root/)                            #
# ------------------------------------------------------------------ #


def to_fs(path: str) -> str:
    """Chemin SFTP (style /home/u…/…) → chemin réel sous server-root/."""
    path = posixpath.normpath(path)
    if not path.startswith('/'):
        path = '/' + path
    return os.path.join(ROOT, *path.split('/'))


class FakeSFTPHandle(SFTPHandle):
    def stat(self):
        try:
            return SFTPAttributes.from_stat(os.fstat(self.readfile.fileno()))
        except OSError:
            return SFTP_NO_SUCH_FILE


class FakeSFTP(SFTPServerInterface):
    def canonicalize(self, path):
        return posixpath.normpath(path if path.startswith('/') else '/' + path)

    def stat(self, path):
        try:
            return SFTPAttributes.from_stat(os.stat(to_fs(path)))
        except OSError:
            return SFTP_NO_SUCH_FILE

    def lstat(self, path):
        try:
            return SFTPAttributes.from_stat(os.lstat(to_fs(path)))
        except OSError:
            return SFTP_NO_SUCH_FILE

    def open(self, path, flags, attr):
        real = to_fs(path)
        try:
            mode = getattr(attr, 'st_mode', None) or 0o644
            fd = os.open(real, flags, mode)
        except OSError:
            return SFTP_NO_SUCH_FILE

        try:
            if flags & os.O_WRONLY:
                fstr = 'ab'
            elif flags & os.O_RDWR:
                fstr = 'a+b'
            else:
                fstr = 'rb'
            f = os.fdopen(fd, fstr)
        except OSError:
            return SFTP_NO_SUCH_FILE

        handle = FakeSFTPHandle(flags)
        handle.filename = real
        handle.readfile = f
        handle.writefile = f
        return handle

    def remove(self, path):
        try:
            os.remove(to_fs(path))
            return SFTP_OK
        except OSError:
            return SFTP_NO_SUCH_FILE

    def rename(self, oldpath, newpath):
        try:
            os.rename(to_fs(oldpath), to_fs(newpath))
            return SFTP_OK
        except OSError:
            return SFTP_NO_SUCH_FILE

    def mkdir(self, path, attr):
        try:
            os.makedirs(to_fs(path), exist_ok=False)
            return SFTP_OK
        except FileExistsError:
            return SFTP_OK
        except OSError:
            return SFTP_NO_SUCH_FILE

    def rmdir(self, path):
        try:
            os.rmdir(to_fs(path))
            return SFTP_OK
        except OSError:
            return SFTP_NO_SUCH_FILE

    def list_folder(self, path):
        real = to_fs(path)
        try:
            entries = []
            for name in sorted(os.listdir(real)):
                attr = SFTPAttributes.from_stat(os.stat(os.path.join(real, name)))
                attr.filename = name
                attr.longname = name
                entries.append(attr)
            return entries
        except OSError:
            return SFTP_NO_SUCH_FILE


# ------------------------------------------------------------------ #
# Serveur                                                              #
# ------------------------------------------------------------------ #


def main():
    os.makedirs(ROOT, exist_ok=True)

    host_key = paramiko.RSAKey.generate(2048)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(16)

    print(f'🏠 Serveur Hostinger SIMULÉ démarré sur {HOST}:{PORT}')
    print(f'   Identifiants : {USERNAME} / {PASSWORD}')
    print(f'   Racine SFTP  : {ROOT}')
    print('   En attente de connexions du script de déploiement…')

    transports = []

    while True:
        try:
            client, address = sock.accept()
        except KeyboardInterrupt:
            break

        print(f'  [ssh] connexion de {address[0]}:{address[1]}')

        transport = paramiko.Transport(client)
        transport.add_server_key(host_key)
        transport.set_subsystem_handler('sftp', paramiko.SFTPServer, FakeSFTP)

        try:
            transport.start_server(server=FakeHostinger())
        except Exception as error:
            print('  [ssh] erreur de négociation :', error)
            continue

        # maintient la référence et attend la fin de session
        def keep(tr=transport):
            try:
                tr.join(timeout=600)
            except Exception:
                pass
            finally:
                tr.close()

        threading.Thread(target=keep, daemon=True).start()
        transports.append(transport)


if __name__ == '__main__':
    main()
