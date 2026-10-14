from quart import Quart, jsonify, request
import uuid
from pathlib import Path
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


app = Quart(__name__)
DATABASE_URL = "postgresql+asyncpg://alumnodb:1234@localhost:9999/si1"
# --- Engine y sesión asíncronos ---
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

with open("server_secret.txt") as file:
    server_secret = next(file).strip()
    server_secret = uuid.UUID(server_secret)
path = Path(f'./file/')
path.mkdir(parents=True,exist_ok=True)

'''
Función comprueba que un token coincide con un uid.
Devuelve true si coincide o false si no.
El token debe ser solo la cadena con el mismo (sin incluir "bearer")
'''
def validar_token(token, uid) -> bool:
    hashed_token = uuid.uuid5(server_secret, uid)
    try:
        if hashed_token == uuid.UUID(token):
            return True
    except ValueError:
        return False
    return False


'''
Función que hace el proceso de tomar la cabecera de la petición,
revisar si la autenticación empieza por "Bearer" y validar el token recibido

La función se ha creado con propósito de limpiar el código de las funciones de respuesta
a peticiones
'''
def autenticar(uid: str):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return False
    token = token[7:] #Eliminar "Bearer" del string
    return validar_token(token, uid)
'''
Función para gestionar las peticiones GET.
Lista todas las películas de la BBDD junto a su cantidad en el inventario (stock)
'''
@app.get('/film/')
async def list_films():
    async with async_session() as session:
    result = await session.execute(
        text(
            """
            SELECT "film.filmID","film.title","film.description","inventory.amount"
            FROM film, inventory
            WHERE inventory.filmID = film.filmID
            """
        ),
    )

    return jsonify(result), 200

@app.get('/cart/')
async def list_cart():
    datos = await request.get_json()
    if not datos:
        return jsonify({'error':'La petición no contiene JSON. Debe contener el campo uid.'}),400
    
    if 'uid' not in datos:
        return jsonify({'error':'El JSON no contiene el campo "uid" (uuid recibido al logarse).'}), 400
    
    if not autenticar(datos.get('uid')):
        return jsonify({'error':'Token de la petición ó uid inválidos.'}), 403

    async with async_session() as session:
    result = await session.execute(
        text(
            #Hay que sacar el titulo de film, quantity de cartLine. Donde coincidan el uid
            #con el de la petición, el cartID de user con el cartID de cartLine, inventoryID de cartLine con
            # inventoryID de inventory y filmID de inventory con filmID de film 
            """
            SELECT "film.filmID","film.title","film.description","inventory.amount"
            FROM film, inventory
            WHERE inventory.filmID = film.filmID
            """
        ),
    )

    return jsonify(result), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051)
