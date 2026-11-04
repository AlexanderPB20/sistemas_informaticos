import redis.asyncio as redis
import hashlib
import os
from dotenv import load_dotenv
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

SERVER_SECRET = uuid.UUID(os.getenv("SERVER_SECRET"))
if SERVER_SECRET is None:
    return "error"


def crear_usuario(username: str, password: str, email: str):
    key = f"user:{username}"

    if redis_client.exists(key):
        return -1
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    redis_client.hset(key, mapping={"username":username,
                                    "password":password_hash,
                                    "email": email})
    return 1


def autenticar(username: str, password: str) -> bool:
    key = f"user:{username}"

    password_read = redis_client.hget(key,"password")
    password_recieved = hashlib.sha256(password.enconde()).hexdigest()
    
    if password_read == password_recieved:
        return True
    return False