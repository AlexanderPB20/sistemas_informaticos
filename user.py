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
users = {}
tokens = {}



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
        return {'error':'No se ha recibido JSON'}, 400

    #Generacion del uuid
    secret_uuid = uuid.uuid4()
    stringified_uuid = str(secret_uuid)
    
    
    #Password hasheada
    password = datos.get('password')
    password256 = hash256(password)
    
    users[stringified_uuid] = {
                    "user":datos.get('name'),
                    "password":password256
                                }

    return {"token":token ,"uid":stringified_uuid}, 201




@app.post('/user')
async def login(name: str):
    #Login code goes here
    return jsonify.loads(name)

'''
Función para gestionar las peticiones PATCH.
Toma el token introducido en la cabecera de la petición y lo valida.
Cuando es válido, cambia la contraseña del usuario del token por la introducida en el JSON
'''
@app.patch('/user')
async def modify(password: str):
    #Mofify password code goes here
    token = request.headers.get("Authorization")
    if not token:
        #Si no hay cabecera con el token
        return {'error':'Requerido token de autenticación en la cabecera de la petición'}, 400

if __name__ == '__main__':
    app.run(host='localhost', port=5050)


'''
Función que genera un token y hashea el mismo.
Devuelve EL TOKEN SIN HASHEAR y guarda el hasheado en "la base de datos"
junto al usuario al que pertenece y la hora de expiración
'''
def generate_token(uid: str):
    #https://stackoverflow.com/a/77251157
    token = secrets.token_urlsafe(32)
    hashed_token = hash256(token)

    #https://stackoverflow.com/questions/13685201
    expiration = datetime.now() + timedelta(minutes = TOKEN_EXPIRATION_TIME)
    tokens[hashed_token] = {"uid":uid,"expiration":expiration}

    return token

#Función usada para hasheo de contraseñas y tokes y limpiar el código principal
def hash256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()