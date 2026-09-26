from quart import Quart, jsonify, request
import uuid
import hashlib
from datetime import datetime, timedelta
TOKEN_EXPIRATION_TIME = 15 #Minutes

app = Quart(__name__)
'''
Almacenamiento de usuarios y contraseñas
En un entorno real, se usaría una conexión a una base de datos
'''
with open("server_secret.txt") as file:
    server_secret = next(file).strip()
users = {}
tokens = {}


'''
Función que genera un token y hashea el mismo.
Devuelve el token hasheado y lo guarda en "la base de datos"
junto al usuario al que pertenece y la hora de expiración
'''
def generate_token(uid: str):
    hashed_token = uuid.uuid5(server_secret, uid)
    #https://stackoverflow.com/questions/13685201
    expiration = datetime.now() + timedelta(minutes = TOKEN_EXPIRATION_TIME)
    tokens[str(hashed_token)] = {"uid":uid,"expiration":expiration}
    return hashed_token

#Función usada para hasheo de contraseñas y limpiar el código principal
def hash256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()








'''
Función para gestionar las peticiones PUT.
Guarda un usuario nuevo en la "base de datos" tomando el nombre de usuario
y password especificados en el JSON junto a la petición
'''
# curl -X PUT "http://127.0.0.1:5050/user" -H "Content-Type: application/json" -d '{"name":"felipe","password":"mypassword"}'
# -H "Authorization: Bearer [token]"
@app.put('/user')
async def create_user():
    #Tomado de: https://mojoauth.com/parse-and-generate-formats/parse-and-generate-json-with-quart#handling-incoming-json-requests
    datos = await request.get_json()
    if not datos:
        #Si no llega un json en la request
        return jsonify({'error':'No se ha recibido JSON'}), 400
    if not datos.get('name') or not datos.get('password'):
        #Si falta algún campo en el json
        return jsonify({'error':'El JSON recibido debe contener campos name (usuario) y password (contraseña)'}), 400
    #Generacion del uuid
    user_uid = uuid.uuid4()
    stringified_uid = str(user_uid)
    
    
    #Password hasheada
    password = datos.get('password')
    password256 = hash256(password)
    
    #Agregar usuario a la "base de datos"
    users[stringified_uid] = {
                    "user":datos.get('name'),
                    "password":password256
                                }

    token = generate_token(stringified_uid)
    return jsonify({"token":token ,"uid":stringified_uid}), 201




@app.post('/user')
async def login():
    datos = await request.get_json()
    if not datos:
        #Si no llega un json en la request
        return jsonify({'error':'No se ha recibido JSON'}), 400
    if not datos.get('name') or not datos.get('password'):
        #Si falta algún campo en el json
        return jsonify({'error':'El JSON recibido debe contener campos name (usuario) y password (contraseña)'}), 400
    
    username = datos.get('name')
    password = datos.get('password')
    hashedpassword = hash256(password)

    #Buscamos por cada uid
    for uid in users:

        #Coincide usuario
        if users[uid]['user'] == username:
            #Coincide contraseña y generamos token
            if users[uid]['password'] == hashedpassword:
                stringified_uid = str(uid)
                token = generate_token(stringified_uid)
                return jsonify({"token":token, "uid": uid}), 200
    
    #No encontrado
    return jsonify({'error':'Usuario o contraseña incorrectos'}), 404

'''
Función para gestionar las peticiones PATCH.
Toma el token introducido en la cabecera de la petición y lo valida.
Cuando es válido, cambia la contraseña del usuario del token por la introducida en el JSON
'''
@app.patch('/user')
async def modify():
    #Primero se verifica si el token es válido antes de nada
    token = request.headers.get("Authorization")
    token = token[7:] #Eliminar "Bearer" del string
    if not token or token not in tokens.keys():
        #Si no hay cabecera con el token o no existe en los guardados
        return jsonify({'error':'No hay token en la cabecera de la petición o es inválido'}), 400
    
    #Luego verificamos si ha introducido contraseña
    datos = await request.get_json()
    if not datos:
        return jsonify({"error":"No se ha recibido JSON"}), 400
    if not datos.get('password'):
        return jsonify({"error":"El JSON recibido no contiene el campo 'password' (contraseña)"}), 400


    #Comprobamos su expiración
    if tokens[token]["expiration"] < datetime.now():
        return jsonify({'error':'El token introducido expiró'}), 403
    

    usuario_uid = tokens[token]["uid"]
    users[usuario_uid]["password"] = hash256(datos.get("password"))

    return jsonify({'response':'Password modificada correctamente'}), 200

if __name__ == '__main__':
    app.run(host='localhost', port=5050)



'''
Podríamos usar una request GET para validar
desde el microservicio de files si un usuario
tiene permisos o no para modificar un fichero

Desde files se hace la request a este microservicio,
entregándole el uid y el fichero y que nos devuelva
un json que diga si es posible o no con boolean o algún
otro dato útil

El paquete requests puede hacer esto
https://stackoverflow.com/questions/77811835'''