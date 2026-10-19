from quart import Quart, jsonify, request
import uuid
import hashlib
import os
from sqlalchemy import text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

app = Quart(__name__)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://alumnodb:1234@postgreDB:5432/si1")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

with open("server_secret.txt") as file:
    server_secret = uuid.UUID(next(file).strip())

def generate_token(uid: str):
    return str(uuid.uuid5(server_secret, uid))

def validate_token(uid: str, token: str):
    return generate_token(uid) == token

def hash256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

@app.put('/user')
async def create_user():
    datos = await request.get_json()
    if not datos or not all(k in datos for k in ('name', 'password', 'country')):
        return jsonify({'error': 'Requiere campos name, password y country'}), 400

    async with async_session() as session:
        # Obtener CountryID
        res_country = await session.execute(
            text('SELECT "countryID" FROM "country" WHERE "name" ILIKE :c'),
            {"c": datos.get('country')}
        )
        country_id = res_country.scalar_one_or_none()
        if not country_id:
            return jsonify({'error': 'País no válido'}), 400

        # Crear nuevo carrito
        res_cart = await session.execute(text('INSERT INTO "cart" DEFAULT VALUES RETURNING "cartID";'))
        cart_id = res_cart.scalar_one()

        uid = str(uuid.uuid4())
        pwd_hash = hash256(datos.get('password'))

        try:
            await session.execute(
                text("""
                    INSERT INTO "user" ("UUID", "username", "password", "countryID", "balance", "cartID")
                    VALUES (:uuid, :username, :password, :country_id, 0, :cart_id);
                """),
                {
                    "uuid": uid,
                    "username": datos.get('name'),
                    "password": pwd_hash,
                    "country_id": country_id,
                    "cart_id": cart_id
                }
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            return jsonify({'error': 'El usuario ya existe o datos incorrectos'}), 409

    return jsonify({"token": generate_token(uid), "uid": uid}), 201

@app.post('/user')
async def login():
    datos = await request.get_json()
    if not datos or not datos.get('name') or not datos.get('password'):
        return jsonify({'error': 'Faltan campos name y password'}), 400

    pwd_hash = hash256(datos.get('password'))
    async with async_session() as session:
        result = await session.execute(
            text('SELECT "UUID" FROM "user" WHERE "username" = :name AND "password" = :pwd'),
            {"name": datos.get('name'), "pwd": pwd_hash}
        )
        user_uid = result.scalar_one_or_none()

    if not user_uid:
        return jsonify({'error': 'Usuario o contraseña incorrectos'}), 401

    uid_str = str(user_uid)
    return jsonify({'uid': uid_str, 'token': generate_token(uid_str)}), 200

@app.patch('/user')
async def modify():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({'error': 'Cabecera Authorization Bearer ausente'}), 401
    token = auth[7:]

    datos = await request.get_json()
    if not datos or 'uid' not in datos or 'balance' not in datos:
        return jsonify({'error': 'Faltan campos uid y balance'}), 400

    if float(datos.get('balance', 0)) <= 0:
        return jsonify({'error': 'El incremento de saldo debe ser mayor que 0'}), 400

    if not validate_token(datos.get('uid'), token):
        return jsonify({'error': 'Token inválido'}), 401

    async with async_session() as session:
        result = await session.execute(
            text("""
                UPDATE "user"
                SET "balance" = "balance" + :amount
                WHERE "UUID" = :uid
                RETURNING "balance";
            """),
            {"uid": datos.get('uid'), "amount": datos.get('balance')}
        )
        balance = result.scalar_one_or_none()
        await session.commit()

    if balance is None:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    return jsonify({'response': f'Saldo actualizado a {balance}'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)