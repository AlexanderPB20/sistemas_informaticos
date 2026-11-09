from quart import Quart, jsonify, request, Blueprint, Response
import redis_client

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

    r = await redis_client.crear_usuario(username, password, email)
    if r is None:
        return jsonify({'error':'El nombre de usuario ya existe'}),401
    return jsonify(r),201
    
@routes_blueprint.post("auth/login")
async def login():
    datos = await request.get_json()
    if not datos:
        #Si no llega un json en la request
        return jsonify({'error':'No se ha recibido JSON'}), 400
    if not datos.get('username') or not datos.get('password'):
        #Si falta algún campo en el json
        return jsonify({'error':'El JSON recibido debe contener campos username (usuario), password (contraseña)'}), 400

    username = datos.get("username")
    password = datos.get("password")

    if not await redis_client.autenticar(username, password):
        return jsonify({'error':'Usuario o contraseña incorrectos'}),401
    
    
    token = await redis_client.crear_sesion(username)
    return jsonify({"token":token}), 200

@routes_blueprint.get("auth/validate")
async def validate():
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return Response(status=401)
    token = token[7:] #Eliminar "Bearer" del string

    r = await redis_client.recuperar_sesion(token)
    if r is None:
        return Response(status=401)
    return Response(status=200, headers=r)

@routes_blueprint.post("auth/logout")
async def logout():
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return jsonify({"error":"No hay token en la cabecera"}),401
    token = token[7:] #Eliminar "Bearer" del string
    
    r = await redis_client.cerrar_sesion(token)

    if r is None:
        return jsonify({"error":"Token inválido o sesión expirada"}),401
    return jsonify(r),200