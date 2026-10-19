from quart import Quart, jsonify, request
import uuid
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import os

app = Quart(__name__)
# Se conecta al contenedor postgreDB en el puerto interno 5432
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://alumnodb:1234@postgreDB:5432/si1")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

with open("server_secret.txt") as file:
    server_secret = uuid.UUID(next(file).strip())

path = Path('./file/')
path.mkdir(parents=True, exist_ok=True)

def validar_token(token: str, uid: str) -> bool:
    try:
        hashed_token = uuid.uuid5(server_secret, uid)
        return str(hashed_token) == token
    except Exception:
        return False

def autenticar(uid: str):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        return False
    return validar_token(token[7:], uid)

@app.get('/film/')
async def list_films():
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT f."filmID", f."title", f."description", f."price", f."filmScore", i."amount" AS stock
                FROM "film" f
                LEFT JOIN "inventory" i ON i."filmID" = f."filmID"
            """)
        )
        entradas = [dict(fila) for fila in result.mappings().all()]
        return jsonify(entradas), 200

@app.get('/film/<name>')
async def list_films_by_name(name: str):
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT f."filmID", f."title", f."description", f."price", f."filmScore", i."amount" AS stock
                FROM "film" f
                LEFT JOIN "inventory" i ON i."filmID" = f."filmID"
                WHERE f."title" ILIKE :name
            """),
            {"name": f"%{name}%"}
        )
        entradas = [dict(fila) for fila in result.mappings().all()]
        return jsonify(entradas), 200

@app.get('/cart/')
async def list_cart():
    datos = await request.get_json()
    if not datos or 'uid' not in datos:
        return jsonify({'error': 'JSON debe contener el campo uid'}), 400
    if not autenticar(datos.get('uid')):
        return jsonify({'error': 'Token o uid inválidos'}), 403

    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT cl."lineID", cl."quantity", f."filmID", f."title", f."price"
                FROM "user" u
                JOIN "cart" c ON c."cartID" = u."cartID"
                JOIN "cartLine" cl ON cl."cartID" = c."cartID"
                JOIN "inventory" i ON i."inventoryID" = cl."inventoryID"
                JOIN "film" f ON f."filmID" = i."filmID"
                WHERE u."UUID" = :uuid AND c."status" = 'active';
            """),
            {"uuid": datos.get('uid')}
        )
        entradas = [dict(fila) for fila in result.mappings().all()]
        return jsonify(entradas), 200

@app.put('/cart/')
async def add_cart_line():
    datos = await request.get_json()
    if not datos or not all(k in datos for k in ('uid', 'filmID', 'amount')):
        return jsonify({'error': 'Faltan campos uid, filmID o amount'}), 400
    if not autenticar(datos.get('uid')):
        return jsonify({'error': 'No autorizado'}), 403

    async with async_session() as session:
        try:
            result = await session.execute(
                text("""
                    INSERT INTO "cartLine" ("inventoryID", "cartID", "quantity")
                    SELECT i."inventoryID", u."cartID", :amount 
                    FROM "user" u
                    JOIN "inventory" i ON i."filmID" = :filmID
                    WHERE u."UUID" = :uid AND u."cartID" IS NOT NULL
                    RETURNING "lineID";
                """),
                {
                    "uid": datos.get('uid'),
                    "filmID": int(datos.get('filmID')),
                    "amount": int(datos.get('amount'))
                }
            )
            line_id = result.scalar_one_or_none()
            await session.commit()
            if not line_id:
                return jsonify({'error': 'No se pudo añadir (revisa filmID o inventario)'}), 404
            return jsonify({'info': 'Añadido al carrito correctamente', 'lineID': line_id}), 201
        except Exception as e:
            await session.rollback()
            return jsonify({'error': str(e)}), 400
@app.put('/vote/')
async def vote_film():
    datos = await request.get_json()
    if not datos or not all(k in datos for k in ('uid', 'filmID', 'score')):
        return jsonify({'error': 'Faltan campos uid, filmID o score'}), 400
    if not autenticar(datos.get('uid')):
        return jsonify({'error': 'No autorizado'}), 403

    async with async_session() as session:
        try:
            await session.execute(
                text("""
                    INSERT INTO "vote" ("UUID", "filmID", "score")
                    VALUES (:uid, :filmID, :score)
                    ON CONFLICT ("UUID", "filmID") DO UPDATE SET "score" = :score;
                """),
                {
                    "uid": datos.get('uid'),
                    "filmID": datos.get('filmID'),
                    "score": datos.get('score')
                }
            )
            await session.commit()
            return jsonify({'info': 'Voto registrado correctamente'}), 201
        except Exception as e:
            await session.rollback()
            return jsonify({'error': str(e)}), 400

@app.post("/cart/")
async def pagar_carrito():
    datos = await request.get_json()
    if not datos or 'uid' not in datos:
        return jsonify({'error': 'Falta el campo uid'}), 400
    if not autenticar(datos.get('uid')):
        return jsonify({'error': 'No autorizado'}), 403

    uid = datos.get('uid')
    async with async_session() as session:
        async with session.begin():
            # Obtener usuario y carrito
            res_user = await session.execute(
                text('SELECT "UUID", "cartID", "balance" FROM "user" WHERE "UUID" = :uid FOR UPDATE'),
                {"uid": uid}
            )
            usuario = res_user.mappings().one_or_none()
            if not usuario:
                return jsonify({"error": "Usuario no encontrado"}), 404

            cart_id = usuario['cartID']
            res_cart = await session.execute(
                text('SELECT "cartID", "status", "total" FROM "cart" WHERE "cartID" = :cid FOR UPDATE'),
                {"cid": cart_id}
            )
            carrito = res_cart.mappings().one_or_none()
            if not carrito or carrito["status"] != "active":
                return jsonify({"error": "El carrito no está activo"}), 400

            res_lines = await session.execute(
                text("""
                    SELECT cl."quantity", f."filmID", f."title", f."price"
                    FROM "cartLine" cl
                    JOIN "inventory" i ON i."inventoryID" = cl."inventoryID"
                    JOIN "film" f ON f."filmID" = i."filmID"
                    WHERE cl."cartID" = :cid
                """),
                {"cid": cart_id}
            )
            lineas = res_lines.mappings().all()
            if not lineas:
                return jsonify({"error": "El carrito está vacío"}), 400

            # 1. Crear compra
            res_compra = await session.execute(
                text("""
                    INSERT INTO "purchase" ("UUID", "total", "status")
                    VALUES (:uid, :total, 'completed')
                    RETURNING "purchaseID", "purchaseDate", "total", "status";
                """),
                {"uid": uid, "total": carrito['total']}
            )
            compra = res_compra.mappings().one()

            # 2. Detalles de compra
            for linea in lineas:
                await session.execute(
                    text("""
                        INSERT INTO "purchase_detail" ("purchaseID", "filmID", "quantity", "unitPrice")
                        VALUES (:pid, :fid, :qty, :price);
                    """),
                    {
                        "pid": compra["purchaseID"],
                        "fid": linea["filmID"],
                        "qty": linea["quantity"],
                        "price": linea["price"]
                    }
                )

            # 3. Marcar carrito viejo como comprado
            await session.execute(
                text('UPDATE "cart" SET "status" = \'purchased\' WHERE "cartID" = :cid'),
                {"cid": cart_id}
            )

            # 4. Asignar nuevo carrito activo al usuario
            res_new_cart = await session.execute(text('INSERT INTO "cart" DEFAULT VALUES RETURNING "cartID";'))
            new_cid = res_new_cart.scalar_one()
            await session.execute(
                text('UPDATE "user" SET "cartID" = :ncid WHERE "UUID" = :uid'),
                {"ncid": new_cid, "uid": uid}
            )

    ticket = {
        "id_compra": compra["purchaseID"],
        "estado": compra["status"],
        "fecha_compra": str(compra["purchaseDate"]),
        "importe": float(compra["total"]),
        "lineas": [dict(l) for l in lineas]
    }
    return jsonify({"info": "Compra realizada con éxito", "ticket": ticket}), 201

@app.get('/ventas/<int:year>/<string:country>')
async def ventas_por_pais_y_ano(year: int, country: str):
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT p."purchaseID", p."purchaseDate", p."total", 
                       u."username", c."name" AS "country"
                FROM "purchase" p
                JOIN "user" u ON u."UUID" = p."UUID"
                JOIN "country" c ON c."countryID" = u."countryID"
                WHERE EXTRACT(YEAR FROM p."purchaseDate") = :year
                  AND c."name" ILIKE :country;
            """),
            {"year": year, "country": country}
        )
        ventas = [dict(row) for row in result.mappings().all()]
        return jsonify(ventas), 200
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051)
