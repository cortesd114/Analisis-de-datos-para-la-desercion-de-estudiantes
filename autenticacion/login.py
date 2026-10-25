import json
import os
import secrets
from pathlib import Path

from flask import redirect, render_template_string, request, session
from werkzeug.security import check_password_hash


RUTA_USUARIOS = Path(__file__).resolve().parent.parent / "usuarios.json"

RUTAS_PUBLICAS = {"/login"}


PAGINA_LOGIN = """
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Iniciar sesión - Seguimiento de estudiantes</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f5f7fa;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 16px;
            box-sizing: border-box;
        }
        form {
            background-color: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            width: 100%;
            max-width: 340px;
        }
        h1 { font-size: 22px; margin: 0 0 5px; }
        p { color: #5f6b7a; margin: 0 0 20px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; }
        input {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border: 1px solid #ccd3dc;
            border-radius: 6px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 11px;
            border: none;
            border-radius: 6px;
            background-color: #2f6fb3;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }
        .error { color: #d64545; margin-bottom: 15px; }
    </style>
</head>
<body>
    <form method="post">
        <h1>Seguimiento estudiantil</h1>
        <p>Acceso solo para personal autorizado</p>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <label for="usuario">Usuario</label>
        <input id="usuario" name="usuario" autocomplete="username" required autofocus>
        <label for="clave">Contraseña</label>
        <input id="clave" name="clave" type="password" autocomplete="current-password" required>
        <button type="submit">Ingresar</button>
    </form>
</body>
</html>
"""


def cargar_usuarios():

    if not RUTA_USUARIOS.exists():
        return {}

    return json.loads(RUTA_USUARIOS.read_text(encoding="utf-8"))


def configurar_login(server):
    """Protege todas las rutas de la app Dash con una página de inicio de sesión."""

    # Sin SECRET_KEY fija, las sesiones se cierran cada vez que se reinicia la app
    server.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    if not cargar_usuarios():
        print("AVISO: no hay usuarios. Crea uno con: python crear_usuario.py")

    @server.before_request
    def exigir_sesion():

        if request.path in RUTAS_PUBLICAS or "usuario" in session:
            return None

        if request.method == "GET":
            return redirect("/login")

        # Peticiones internas de Dash con la sesión vencida
        return "Sesión expirada. Vuelve a iniciar sesión.", 401

    @server.route("/login", methods=["GET", "POST"])
    def login():

        error = None

        if request.method == "POST":

            usuario = request.form.get("usuario", "").strip()
            clave = request.form.get("clave", "")
            hash_guardado = cargar_usuarios().get(usuario)

            if hash_guardado and check_password_hash(hash_guardado, clave):
                session.clear()
                session["usuario"] = usuario
                return redirect("/")

            error = "Usuario o contraseña incorrectos"

        return render_template_string(PAGINA_LOGIN, error=error)

    @server.route("/logout")
    def logout():

        session.clear()
        return redirect("/login")
