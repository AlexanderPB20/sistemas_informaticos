from quart import Quart, jsonify, request
import uuid
import hashlib
from sqlalchemy import text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from datetime import datetime, timedelta
TOKEN_EXPIRATION_TIME = 15 #Minutes

app = Quart(__name__)
DATABASE_URL = "postgresql+asyncpg://alumnodb:1234@postgreDB:5432/si1"
# --- Engine y sesión asíncronos ---
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()
'''
Almacenamiento de usuarios y contraseñas
En un entorno real, se usaría una conexión a una base de datos
'''
with open("server_secret.txt") as file:
    server_secret = next(file).strip()
    server_secret = uuid.UUID(server_secret)


'''
Función que genera un token y hashea el mismo.
Devuelve el token hasheado y lo guarda en "la base de datos"
junto al usuario al que pertenece y la hora de expiración
'''
def generate_token(uid: str):
    hashed_token = uuid.uuid5(server_secret, uid)
    return hashed_token

def validate_token(uid: str, token: str):
    hashed_token = uuid.uuid5(server_secret, uid)
    return str(hashed_token) == token

#Función usada para hasheo de contraseñas y limpiar el código principal
def hash256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


async def get_conutry_id(country_name: str):
    async with async_session() as session:
        result = await session.execute(
            text(
                """
                SELECT "countryID"
                FROM country
                WHERE name = :country_name
                """
            ),
            {"country_name": country_name},
        )

        return result.scalar_one_or_none()

async def get_new_cart_id(session):
    result = await session.execute(
        text(
            """
            INSERT INTO cart
            DEFAULT VALUES
            RETURNING "cartID"
            """
        ),
    )

    return result.scalar_one()
'''
Función para gestionar las peticiones PUT.
Guarda un usuario nuevo en la "base de datos" tomando el nombre de usuario
y password especificados en el JSON junto a la petición
'''

@app.put('/user')
async def create_user():
    datos = await request.get_json()
    if not datos:
        #Si no llega un json en la request
        return jsonify({'error':'No se ha recibido JSON'}), 400
    if not datos.get('name') or not datos.get('password') or not datos.get('country'):
        #Si falta algún campo en el json
        return jsonify({'error':'El JSON recibido debe contener campos name (usuario), password (contraseña) y country (pais)'}), 400
    
    #Sacar el country id y el cart id nuevo que se genere
    country_id = await get_conutry_id(datos.get('country'))
    if country_id == None:
        return jsonify({'error':'''El pais introducido es incorrecto. Por favor, usa el nombre en ingés con la primera letra
        en mayúscula. (Ej: Spain, France, Belgium)'''}), 400
    

    #Generacion del uuid
    user_uid = uuid.uuid4()
    stringified_uid = str(user_uid)
    
    
    #Password hasheada
    password = datos.get('password')
    password256 = hash256(password)
    
    #Agregar usuario a la base de datos
    token = generate_token(stringified_uid)

    try:
        async with async_session() as session:
            async with session.begin():
                cart_id = await get_new_cart_id(session)

                result = await session.execute(
                    text("""
                        INSERT INTO "user" ("UUID", username, password, "countryID", "balance", "cartID")
                        VALUES (:uuid, :username, :password, :country_id, :balance, :cart_id)
                        """),
                        {
                            "uuid": stringified_uid,
                            "username": datos.get('name'),
                            "password": password256,
                            "country_id": country_id,
                            "balance": 0,
                            "cart_id": cart_id,
                        },
                )
    except Exception as e:
                    await session.rollback()
                    return jsonify({"error":"El usuario ya existe"}), 409
    return jsonify({"token":token ,"uid":stringified_uid}), 201



'''
Función para gestionar las peticiones POST.
Toma el usuario y contraseña introducido en le JSON de la cabecera y los valida.
Cuando es válido, devuelve un token
'''
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
    try:
        async with async_session() as session:
            result = await session.execute(
                text(
                    """
                    SELECT "UUID"
                    FROM "user"
                    WHERE "username" = :username AND "password" = :password
                    """
                ),
                {"username": username,
                "password": hashedpassword},
            )

            uid = result.scalar_one_or_none()
    except Exception as e:
        await session.rollback()
        return jsonify({"error":"Usuario o contraseña incorrectos"}), 401

    if uid is None:
        #No encontrado
        return jsonify({'error':'Usuario o contraseña incorrectos'}), 401
    
    return jsonify({'uid':uid,'token':generate_token(str(uid))}), 200


'''
Función para gestionar las peticiones PATCH.
Toma el token introducido en la cabecera de la petición y lo valida.
Cuando es válido, permite al usuario aumentar el saldo de su cuenta
'''
@app.patch('/user')
async def modify():
    #Primero se verifica si el token es válido antes de nada
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        #Si no hay cabecera con el token o no existe en los guardados
        return jsonify({'error':'No hay token en la cabecera de la petición'}), 400
    token = token[7:] #Eliminar "Bearer" del string
    
    #Luego verificamos si ha introducido contraseña
    datos = await request.get_json()
    if not datos:
        return jsonify({"error":"No se ha recibido JSON"}), 400
    if not datos.get('uid') or not datos.get('balance'):
        return jsonify({"error":"El JSON recibido debe contener los campos 'uid'(UUID) y 'balance' (saldo)"}), 400

    if not datos.get('balance') > 0:
        return jsonify({"error":"El saldo especificado debe ser un valor superior a 0"}), 400

    if not validate_token(datos.get('uid'),token):
        return jsonify({'error':'Token o uid inválido'}), 401
    
    async with async_session() as session:
        result = await session.execute(
            text("""
                UPDATE "user"
                SET balance = balance + :amount
                WHERE "UUID" = :uuid
                RETURNING balance;
            """),
            {"uuid":datos.get('uid'),
             "amount":datos.get('balance')},
        )
        balance = result.scalar_one_or_none()
        await session.commit()
    
    if balance is None:
        return jsonify({'error':'Usuario no encontrado'}), 404

    return jsonify({'response':f'Se ha incrementado el saldo de la cuenta a {balance}'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)