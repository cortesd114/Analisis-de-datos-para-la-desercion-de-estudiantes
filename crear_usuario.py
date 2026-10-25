"""
Crea o actualiza un usuario autorizado para entrar al dashboard.

Uso: python crear_usuario.py
"""

import getpass
import json

from werkzeug.security import generate_password_hash

from autenticacion.login import RUTA_USUARIOS, cargar_usuarios


def main():

    usuario = input("Usuario: ").strip()

    if not usuario:
        print("El usuario no puede estar vacío.")
        return

    clave = getpass.getpass("Contraseña: ")

    if len(clave) < 8:
        print("La contraseña debe tener al menos 8 caracteres.")
        return

    if clave != getpass.getpass("Repite la contraseña: "):
        print("Las contraseñas no coinciden.")
        return

    usuarios = cargar_usuarios()
    usuarios[usuario] = generate_password_hash(clave)

    RUTA_USUARIOS.write_text(
        json.dumps(usuarios, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"Usuario '{usuario}' guardado.")


if __name__ == "__main__":
    main()
