import redis.asyncio as redis
import uuid
import secrets
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

SERVER_SECRET = uuid.UUID(os.getenv("SERVER_SECRET"))
SESSION_TTL = 300 #seconds


'''
Crea un usuario en la base de datos de redis si no existe
el username

Devuelve el uuid
'''
async def crear_usuario(username: str, password: str, email: str):
    key = f"user:{username}"

    if await redis_client.exists(key):
        return None

    uuid = uuid.uuid4()
    str_uuid = str(uuid)
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    await redis_client.hset(key, mapping={"username":username,
                                    "uuid":str_uuid,
                                    "password":password_hash,
                                    "email": email})
    return {"info":"Creado correctamente", "uuid":str_uuid}

'''
Dado un username y una contraseña, valida si en la base
de datos de redis existe esa entrada.

Devuelve True si existe, False si no
'''
async def autenticar(username: str, password: str) -> bool:
    key = f"user:{username}"

    password_read = await redis_client.hget(key,"password")
    password_recieved = hashlib.sha256(password.encode()).hexdigest()
    
    if password_read == password_recieved:
        return True
    return False

'''
Genera y devuelve un token de 42 caracteres
'''
def generar_token():
    return secrets.token_urlsafe(42)

'''
Genera y devuelve la clave de sesión a partir de un token
'''
def generar_session_key(token) -> str:
    hash = hashlib.sha256(token.encode()).hexdigest()
    return f'session:{hash}'

'''
Crea una sesión para un usuario dado su username. 

Devuelve un token
'''
async def crear_sesion(username: str):
    token = generar_token()
    session = generar_session_key(token)

    usuario = await redis_client.hgetall(f'user:{username}')

    await redis_client.hset(session, mapping={"username": username,
                                            "uuid":usuario["uuid"]})
    await redis_client.expire(session, SESSION_TTL)

    return token

'''
Busca en la base de datos una sesión a partir de un token

Si existe, devuelve su uuid en un diccionario con clave X-User-Id,
si no existe, devuelve None
'''
async def recuperar_sesion(token: str):
    sk = generar_session_key(token)

    session = await redis_client.hgetall(sk)
    if not session:
        return None

    return {"X-User-Id":session["uuid"]}

'''
Busca un token dado activo en la base de datos y
elimina la entrada. Cierra la sesión.

Devuelve None si no existía una sesión con ese token o 
un mensaje de info en un diccionario si se ha podido cerrar
'''
async def cerrar_sesion(token: str):
    sk = generar_session_key(token)

    session = await redis_client.delete(sk)
    if session == 0:
        return None
    return {"info":"Sesión cerrada correctamente"}