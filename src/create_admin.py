"""Preparar un usuario de administrador sin guardar contraseñas en Git.

Uso: python src/create_admin.py --username neutrinitoo
El operador copia las tres variables a la configuracion PRIVADA del servidor.
"""
import argparse
import getpass
import secrets
from werkzeug.security import generate_password_hash


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="neutrinitoo")
    parser.add_argument("--generate-password", action="store_true",
                        help="Crear una contraseña aleatoria en vez de solicitarla")
    args = parser.parse_args()
    username = args.username.strip()
    if not username or len(username) > 128 or any(c.isspace() for c in username):
        parser.error("Usuario inválido. Debe tener 1-128 caracteres sin espacios.")
    if args.generate_password:
        password = secrets.token_urlsafe(32)
    else:
        password = getpass.getpass("Nueva contraseña (mínimo 14 caracteres): ")
        repeat = getpass.getpass("Repite contraseña: ")
        if password != repeat:
            parser.error("Las contraseñas no coinciden.")
    if len(password) < 14:
        parser.error("La contraseña debe tener al menos 14 caracteres.")
    print("\nConfigura estas variables ÚNICAMENTE en el servidor, no en el repositorio:\n")
    print(f"AUTH_USERNAME={username}")
    print(f"AUTH_PASSWORD_HASH={generate_password_hash(password, method='scrypt')}")
    print(f"SESSION_SECRET={secrets.token_urlsafe(48)}")
    if args.generate_password:
        print(f"\nContraseña generada (guardar en gestor de contraseñas): {password}")
    print("\nCuenta preparada. Se activa cuando se configuran esas variables y se reinicia Flask.")


if __name__ == "__main__":
    main()
