import argparse
import getpass
import os
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django


django.setup()

from django.contrib.auth import authenticate


def main():
    parser = argparse.ArgumentParser(description='Script simple de connexion Django.')
    parser.add_argument('--username', help="Nom d'utilisateur")
    parser.add_argument('--password', help='Mot de passe')
    args = parser.parse_args()

    username = args.username or input("Nom d'utilisateur: ").strip()
    password = args.password or getpass.getpass('Mot de passe: ')

    user = authenticate(username=username, password=password)

    if user is None:
        print('Echec: identifiants invalides.')
        raise SystemExit(1)

    if not user.is_active:
        print('Echec: compte inactif.')
        raise SystemExit(1)

    roles = list(user.groups.values_list('name', flat=True))
    roles_txt = ', '.join(roles) if roles else 'Aucun role'

    print(f'Connexion reussie pour: {user.username}')
    print(f'Roles: {roles_txt}')


if __name__ == '__main__':
    main()
