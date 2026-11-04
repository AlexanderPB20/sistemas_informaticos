from quart import Quart, jsonify, request, Blueprint

routes_blueprint = Blueprint('routes_blueprint', __name__)

@routes_blueprint.post("auth/register")
async def register():
    datos = await request.get_json()
    if not datos:
        #Si no llega un json en la request
        return jsonify({'error':'No se ha recibido JSON'}), 400
    if not datos.get('username') or not datos.get('password') or not datos.get('email'):
        #Si falta algún campo en el json
        return jsonify({'error':'El JSON recibido debe contener campos username (usuario), password (contraseña) y email (correo electrónico)'}), 400

    username = datos.get("username")
    password = datos.get("password")
    email    = datos.get("email")

    crear_usuario(username, password, email)
    return