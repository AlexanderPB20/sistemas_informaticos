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
            SELECT film."filmID",film."title",film."description",inventory."amount"
            FROM "film"
            JOIN "inventory" ON
            inventory."filmID" = film."filmID"
            """
        ),
    )
    #Transformar la salida a diccionarios para poder "jsonificarlos"
    entradas = [dict(fila) for fila in result.mappings().all()]
    return jsonify(entradas), 200
'''
Función para gestionar las peticiones GET.
Lista todas las películas que tengan un nombre similar a name
'''
@app.get('/film/<name>')
async def list_films_by_name(name: str):
    async with async_session() as session:
    result = await session.execute(
        text(
            """
            SELECT film."filmID",film."title",film."description",inventory."amount"
            FROM "film"
            JOIN "inventory" ON
            inventory."filmID" = film."filmID"
            WHERE
            film."title" ILIKE :name
            """
        ),{"name":f"%{name}%"},
    )

    #Transformar la salida a diccionarios para poder "jsonificarlos"
    entradas = [dict(fila) for fila in result.mappings().all()]
    return jsonify(entradas), 200

'''
Función para gestionar las peticiones GET.
Lista todas las entradas del carrito de un usuario
'''
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
            text("""
                SELECT cartLine."lineID", cartLine."quantity", film."filmID", film."title", film."price"
                    FROM "user"
                    JOIN "cart"
                        ON "cart"."cartID" = "user"."cartID"
                    JOIN "cartLine"
                        ON "cartLine"."cartID" = "cart"."cartID"
                    JOIN "inventory"
                        ON "inventory"."inventoryID" = "cartLine"."inventoryID"
                    JOIN "film"
                        ON "film"."filmID" = "inventory"."filmID"
                    WHERE "user"."UUID" = :uuid
                    AND "cart"."status" = 'active';
                """
            ),{"uuid":datos.get('uid'),},
        )

    #Transformar la salida a diccionarios para poder "jsonificarlos"
    entradas = [dict(fila) for fila in result.mappings().all()]
    return jsonify(entradas), 200



'''
Función para gestionar las peticiones PUT.
Agrega una película a la base de datos
'''
@app.put('/film/')
async def add_film():
    datos = await request.get_json()
    if not datos:
        return jsonify({'error':'''La petición no contiene JSON. Debe contener los campos:
        \ntitle, descrpition, directorID (puede ser NULL) y price.'''}),400
    
    if 'title' not in datos or 'description' not in datos or 'directorID' not in datos or 'price' not in datos:
        return jsonify({'error':'Archivo JSON incompleto.'}), 400
    
    if not autenticar(datos.get('uid')):
        return jsonify({'error':'No tienes permiso para realizar esta acción. Comprueba las credenciales'}), 403

    async with async_session() as session:
        result = await session.execute(
            text("""
                INSERT INTO "film" ("title", "description", "directorID", "price")
                VALUES(
                :title,
                :description,
                :directorID,
                :price);
                RETURNING "filmID";
                """
            ),{"title":datos.get('title'),
            "description":datos.get('description'),
            "directorID":datos.get('directorID'),
            "price":datos.get('price')},
        )
        filmID = result.scalar_one_or_none()
        await session.commit()
    
    if not filmID:
        return jsonify({'error':'No se ha podido añadir la película'}), 500
    return jsonify({'info':f'Película añadida correctamente con id {filmID}','filmID':filmID}), 201
'''
Función para gestionar las peticiones PUT.
Agrega una entrada al carrito de un usuario
'''
@app.put('/cart/')
async def add_cart_line():
    datos = await request.get_json()
    if not datos:
        return jsonify({'error':'''La petición no contiene JSON. Debe contener los campos:
        \nuid, filmID, amount.'''}),400
    
    if 'uid' not in datos or 'filmID' not in datos or 'amount' not in datos:
        return jsonify({'error':'Archivo JSON incompleto.'}), 400
    
    if not autenticar(datos.get('uid')):
        return jsonify({'error':'No tienes permiso para realizar esta acción. Comprueba las credenciales'}), 403

    async with async_session() as session:
        result = await session.execute(
            text("""
                INSERT INTO "cartLine" ("inventoryID", "cartID", "quantity")
                SELECT i."inventoryID", u."cartID", :amount 
                FROM "user" u
                JOIN "inventory" i ON i."filmID" = :filmID
                WHERE u."UUID" = :uid
                AND u."cartID" IS NOT NULL
                RETURNING "lineID";
                """
            ),{"uid":datos.get('uid'),
            "filmID":datos.get('filmID'),
            "amount":datos.get('amount'),
            },
        )
        lineID = result.scalar_one_or_none()
        await session.commit()
    
    if not filmID:
        return jsonify({'error':'No se ha podido añadir el pedido'}), 500
    return jsonify({'info':f'Película añadida al carrito correctamente','lineID':lineID}), 201


'''
Función para gestionar las peticiones PUT.
Publica un voto a una película
'''
@app.put('/vote/')
async def vote_film():
    datos = await request.get_json()
    if not datos:
        return jsonify({'error':'''La petición no contiene JSON. Debe contener los campos:
        \nuid, filmID, score.'''}),400
    
    if 'uid' not in datos or 'filmID' not in datos or 'score' not in datos:
        return jsonify({'error':'Archivo JSON incompleto.'}), 400
    
    if not autenticar(datos.get('uid')):
        return jsonify({'error':'No tienes permiso para realizar esta acción. Comprueba las credenciales'}), 403

    async with async_session() as session:
        result = await session.execute(
            text("""
                INSERT INTO "vote" ("UUID", "filmID", "score")
                VALUES (:uid, :filmID, :score)
                RETURNING "voteID";
                """
            ),{"uid":datos.get('uid'),
            "filmID":datos.get('filmID'),
            "amount":datos.get('score'),
            },
        )
        voteID = result.scalar_one_or_none()
        await session.commit()
    
    if not filmID:
        return jsonify({'error':'No se ha podido publicar el voto. Compruebe el ID de la película'}), 404
    return jsonify({'info':f'Película añadida al carrito correctamente','voteID':voteID}), 201



'''
Función para gestionar las peticiones DELETE.
Elimina una película de la BBDD
'''
@app.delete('/film/')
async def delete_film():
    datos = await request.get_json()
    if not datos:
        return jsonify({'error':'''La petición no contiene JSON. Debe contener los campos:
        \nuid, filmID'''}),400
    
    if 'uid' not in datos or 'filmID' not in datos:
        return jsonify({'error':'Archivo JSON incompleto.'}), 400
    
    if not autenticar(datos.get('uid')):
        return jsonify({'error':'No tienes permiso para realizar esta acción. Comprueba las credenciales'}), 403

    async with async_session() as session:
        result = await session.execute(
            text("""
                DELETE FROM "film"
                WHERE "filmID" = :filmID
                returning "filmID";
                """
            ),{"uid":datos.get('uid'),
            "filmID":datos.get('filmID'),
            },
        )
        filmID = result.scalar_one_or_none()
        await session.commit()
    
    if not filmID:
        return jsonify({'error':'No se ha podido eliminar la película. Asegúrese de que el ID esté bien escrito'}), 404
    return jsonify({'info':f'Película con id {filmID} eliminada de la base de datos.'}), 201

'''
Función para gestionar las peticiones DELETE.
Elimina una película del carrito
'''
@app.delete('/cart/')
async def delete_cart_line():
    datos = await request.get_json()
    if not datos:
        return jsonify({'error':'''La petición no contiene JSON. Debe contener los campos:
        \nuid, filmID'''}),400
    
    if 'uid' not in datos or 'filmID' not in datos:
        return jsonify({'error':'Archivo JSON incompleto.'}), 400
    
    if not autenticar(datos.get('uid')):
        return jsonify({'error':'No tienes permiso para realizar esta acción. Comprueba las credenciales'}), 403

    async with async_session() as session:
        result = await session.execute(
            text("""
                DELETE FROM "cartLine" cl
                USING "inventory" i, "user" u
                WHERE cl."inventoryID" = i."inventoryID"
                AND cl."cartID" = u."cartID"
                AND u."UUID" = :uid
                AND i."filmID" = :filmID
                RETURNING cl."lineID";
                """
            ),{"uid":datos.get('uid'),
            "filmID":datos.get('filmID'),
            },
        )
        filmID = result.scalar_one_or_none()
        await session.commit()
    
    if not filmID:
        return jsonify({'error':'No se ha podido eliminar la película el pedido. Asegúrese de que el ID esté bien escrito'}), 404
    return jsonify({'info':f'Película con id {filmID} eliminada de su carrito.'}), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051)
