from quart import Quart, jsonify, request
import uuid
from pathlib import Path
from sqlalchemy import text
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
                SELECT "film"."filmID","film"."title","film"."description","inventory"."amount", "film"."filmScore"
                FROM "film"
                JOIN "inventory" ON
                "inventory"."filmID" = "film"."filmID"
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
                SELECT film."filmID",film."title",film."description",inventory."amount", film."filmScore"
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
                SELECT "cartLine"."lineID", "cartLine"."quantity", film."filmID", film."title", film."price"
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
        \ntitle, descrpition, directorID (puede ser NULL), amount y price.'''}),400
    
    if 'title' not in datos or 'description' not in datos or 'directorID' not in datos or 'amount' not in datos or 'price' not in datos:
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
                :price)
                RETURNING "filmID";
                """
            ),{"title":datos.get('title'),
            "description":datos.get('description'),
            "directorID":datos.get('directorID'),
            "price":datos.get('price')},
        )
        filmID = result.scalar_one_or_none()

        result = await session.execute(
            text("""
                INSERT INTO "inventory" ("filmID", "amount")
                 VALUES(
                 :filmID,
                 :amount)
                 """),{"filmID": filmID,
                       "amount": datos.get('amount')}
        )
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
                SELECT "inventory"."inventoryID", "user"."cartID", :amount 
                FROM "user"
                JOIN "inventory" ON "inventory"."filmID" = :filmID
                WHERE "user"."UUID" = :uid
                AND "user"."cartID" IS NOT NULL
                RETURNING "lineID";
                """
            ),{"uid":datos.get('uid'),
            "filmID":datos.get('filmID'),
            "amount":datos.get('amount'),
            },
        )
        lineID = result.scalar_one_or_none()
        await session.commit()
    
    if not lineID:
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
    try:
        async with async_session() as session:
            result = await session.execute(
                text("""
                    INSERT INTO "vote" ("UUID", "filmID", "score")
                    VALUES (:uid, :filmID, :score)
                    RETURNING "voteID";
                    """
                ),{"uid":datos.get('uid'),
                "filmID":datos.get('filmID'),
                "score":datos.get('score'),
                },
            )
            voteID = result.scalar_one_or_none()
            await session.commit()
    except Exception:
        return jsonify({'error':'Error al votar la película'}),500
    if not voteID:
        return jsonify({'error':'No se ha podido publicar el voto. Compruebe el ID de la película'}), 404
    return jsonify({'info':f'Voto emitido correctamente','voteID':voteID}), 201



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
        # Hay que eliminar también la entrada del inventario, de purchaseDetail y cartLine
        await session.execute(
            text("""
                DELETE FROM "cartLine"
                WHERE "inventoryID" IN (
                SELECT "inventoryID"
                FROM "inventory"
                WHERE "filmID" = :filmID
                )
                """),{"filmID": datos.get('filmID')}
        )
        await session.execute(
            text("""
                DELETE FROM "purchase_detail"
                WHERE "filmID" = :filmID;
                """),{"filmID": datos.get('filmID')}
        )
        await session.execute(
            text("""
                DELETE FROM "inventory"
                WHERE "filmID" = :filmID
            """),{"filmID":datos.get('filmID')}
        )
        result = await session.execute(
            text("""
                DELETE FROM "film"
                WHERE "filmID" = :filmID
                returning "filmID";
                """
            ),{"filmID":datos.get('filmID'),
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
                DELETE FROM "cartLine"
                USING "inventory", "user"
                WHERE "cartLine"."inventoryID" = "inventory"."inventoryID"
                AND "cartLine"."cartID" = "user"."cartID"
                AND "user"."UUID" = :uid
                AND "inventory"."filmID" = :filmID
                RETURNING "inventory"."filmID";
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


@app.post("/cart/")
async def pagar_carrito():
    datos = await request.get_json()
    if not datos:
        return jsonify({'error':'''La petición no contiene JSON. Debe contener los campos:
        \nuid'''}),400
    
    if 'uid' not in datos:
        return jsonify({'error':'Archivo JSON incompleto.'}), 400
    
    if not autenticar(datos.get('uid')):
        return jsonify({'error':'No tienes permiso para realizar esta acción. Comprueba las credenciales'}), 403

    uid = datos.get('uid')

    async with async_session() as session:
        async with session.begin():
            # Bloquear usuario
            user_result = await session.execute(
                text("""
                    SELECT "UUID", "cartID"
                    FROM "user"
                    WHERE "UUID" = :uid
                    FOR UPDATE
                """),
                {"uid": uid},
            )
            usuario = user_result.mappings().one_or_none()

            # Comprobar que el usuario existe.
            ''' Esta comprobación es necesaria por un caso extremo en particular:
            Como estamos comprobando la autenticación con una simple operación matemática,
            técnicamente es posible que un usuario que haya sido eliminado de la BBDD pero que la persona
            conserve el UID y token pueda autenticarse. '''
            if usuario is None:
                return jsonify({"error": "Usuario no encontrado"}), 404

            #Obtener su carrito actual
            cartID = usuario['cartID']

            if cartID is None:
                return jsonify({"error": "El usuario no tiene un carrito"}), 400

            # Bloquear el carrito
            consulta_carrito = await session.execute(
                text("""
                    SELECT "cartID", "status", "total"
                    FROM "cart"
                    WHERE "cartID" = :cartID
                    FOR UPDATE
                """),
                {"cartID": cartID},
            )
            carrito = consulta_carrito.mappings().one_or_none()

            #Comprobar si el carrito existe o no está activo
            if carrito is None or carrito["status"] != "active":
                return jsonify({"error": "El carrito no está activo"}), 400

            # Bloquear el carrito y sacar las lineas
            lineas_carrito = await session.execute(
                text("""
                    SELECT "cartLine"."inventoryID", "cartLine"."quantity",
                        "inventory"."filmID", "film"."title", "film"."price"
                    FROM "cartLine"
                    JOIN "inventory"
                    ON "inventory"."inventoryID" = "cartLine"."inventoryID"
                    JOIN "film"
                    ON "film"."filmID" = "inventory"."filmID"
                    WHERE "cartLine"."cartID" = :cartID
                    ORDER BY "cartLine"."lineID"
                    FOR UPDATE OF "cartLine"
                """),
                {"cartID": cartID},
            )
            lineas = lineas_carrito.mappings().all()

            #Comprobar si el carrito está vacío
            if not lineas:
                return jsonify({"error": "El carrito está vacío"}), 400

            # Crear la entrada del pedido
            consulta_compra = await session.execute(
                text("""
                    INSERT INTO "purchase" ("UUID", "total", "status")
                    VALUES (:uid, :total, 'completed')
                    RETURNING "purchaseID", "purchaseDate", "total", "status"
                """),
                {
                    "uid": uid,
                    "total": carrito['total'],
                },
            )
            compra = consulta_compra.mappings().one()

            # Crear las entradas de las lineas del pedido
            for linea in lineas:
                await session.execute(
                    text("""
                        INSERT INTO "purchase_detail" ("purchaseID", "filmID", "quantity", "unitPrice")
                        VALUES (:purchaseID, :filmID, :quantity, :unit_price)
                    """),
                    {
                        "purchaseID": compra["purchaseID"],
                        "filmID": linea["filmID"],
                        "quantity": linea["quantity"],
                        "unit_price": linea["price"],
                    },
                )

            # Completar carrito
            await session.execute(
                text("""
                    UPDATE "cart"
                    SET "status" = 'purchased'
                    WHERE "cartID" = :cartID
                """),
                {"cartID": cartID},
            )

            # Reemplazar el carrito antiguo por uno nuevo
            consulta_nuevo_carrito = await session.execute(
                text("""
                    INSERT INTO "cart"
                    DEFAULT VALUES
                    RETURNING "cartID"
                """)
            )
            new_cartID = consulta_nuevo_carrito.scalar_one()

            # Asignar el carrito nuevo al usuario
            await session.execute(
                text("""
                    UPDATE "user"
                    SET "cartID" = :new_cartID
                    WHERE "UUID" = :uid
                """),
                {
                    "new_cartID": new_cartID,
                    "uid": uid,
                },
            )


    ticket_pedido = {"id_compra": compra["purchaseID"],
                     "estado": compra["status"],
                     "fecha_compra": compra["purchaseDate"],
                     "importe": compra["total"],

                     "lineas":[
                                {"titulo": linea["title"],
                                 "cantidad": linea["quantity"],
                                 "precio_unidad": linea["price"]
                                } for linea in lineas
                             ]
                    }
    
    return jsonify({"info": "El pedido se ha realizado correctamente. Gracias por su compra.", "ticket":ticket_pedido}), 201



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051)
