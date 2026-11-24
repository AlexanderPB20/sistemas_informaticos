from pymongo import AsyncMongoClient as mongo
from pymongo import ReturnDocument
import json
from datetime import datetime, timezone

uri = "mongodb://alumnodb:1234@mongo:27017/?authSource=admin"

cliente = mongo(uri)

db = cliente["si1"]

books = db["books"]

async def insertar_libro(isbn: str, title: str, author: str, year: int, publisher: str, stock: int):
    '''
    Inserta un libro con los parametros introducidos

    Devuelve el nuevo id del libro insertado
    '''
    loan_history = []

    libro = {
        "isbn": isbn,
        "title": title,
        "author": author,
        "year": year,
        "publisher": publisher,
        "available_stock": stock,
        "loan_history": loan_history
    }

    resultado = await books.insert_one(libro)

    return resultado.inserted_id

async def buscar_libro(isbn: str):
    '''
    Busca un libro con isbn introducido en la base de datos

    Devuelve el libro o None si no se encuentra
    '''
    resultado = await books.find_one({"isbn":isbn})

    return resultado


async def listar_libros():
    '''
    Lista todos los libros de la base de datos

    Devuelve una lista con todas las entradas encontradas.
    '''
    resultado = books.find()

    return await resultado.to_list()


async def listar_sin_stock():
    '''
    Lista todos los libros fuera de stock

    Devuelve una lista con todas las entradas encontradas.
    '''
    resultado = books.find({"available_stock":0})

    return await resultado.to_list()


async def eliminar_libro(isbn: str):
    '''
    Elimina un libro de la base de datos, si no tiene devoluciones pendientes

    Devuelve -1 en caso de no encontrar el libro o no poder realizar el eliminado
    Devuelve 0 en caso de que hayan devoluciones pendientes
    Devuelve la cantidad de libros eliminados de la base de datos en caso de éxito
    '''
    resultado = await buscar_libro(isbn)

    if resultado is None:
        return -1

    for loan in resultado["loan_history"]:
        if loan["return_date"] is None:
            return 0

    resultado = await books.delete_one({"isbn":isbn})
    if resultado.deleted_count == 0:
        return -1

    return resultado.deleted_count

async def listar_prestamos(user_id: str):
    '''
    Lista todos los libros pendientes de devolver por el usuario especificado

    Devuelve una lista con todas las entradas encontradas
    '''
    #https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/query/specify-query/#array-operators
    resultado = books.find({
        "loan_history": {"$elemMatch": 
            {
                "user_id": user_id,
                "return_date": None
            }
        }
    })

    return await resultado.to_list()

async def listar_historial(user_id: str):
    '''
    Lista el historial de préstamos (devueltos) del usuario especificado

    Devuelve una lista con todas las entradas encontradas
    '''
    resultado = books.find({
        "loan_history": {"$elemMatch":
            {
                "user_id":user_id,
                "return_date": {"$ne": None}
            }
        }
    })

    return await resultado.to_list()



async def iniciar_prestamo(isbn: str, user_id:str):
    '''
    Inicia el préstamo de un libro <isbn> a nombre del usuario con id <user_id>

    Devuelve la entrada del libro modificada en la BBDD
    '''
    fecha = datetime.now(timezone.utc)
    formateada = fecha.isoformat(timespec="milliseconds").replace("+00:00","Z")

    resultado = await books.find_one_and_update(
        {"isbn":isbn,
         "available_stock":{"$gt":0}},
        {"$inc": {"available_stock":-1},
         "$push": {"loan_history": {
                    "user_id":user_id,
                    "loan_date":formateada,
                    "return_date":None
                }}
        },return_document=ReturnDocument.AFTER
    )

    return resultado


async def finalizar_prestamo(isbn: str, user_id: str):
    '''
    Finaliza el préstamo del usuario <user_id> para el libro <isbn>

    Devuelve la entrada del libro modificada en la BBDD
    '''
    fecha = datetime.now(timezone.utc)
    formateada = fecha.isoformat(timespec="milliseconds").replace("+00:00","Z")

    resultado = await books.find_one_and_update(
        {"isbn":isbn,
         "loan_history":{
            "$elemMatch":{
                "user_id":user_id,
                "return_date":None                
            }
         }
        },
        {"$inc": {"available_stock":1},
         "$set": {"loan_history.$.return_date":formateada
                }
        },return_document=ReturnDocument.AFTER
    )

    return resultado


async def populate():
    '''
    Función que se ejecuta cada vez que se inicia el servicio. Pobla
    la base de datos con el fichero populate.json proporcionado
    
    Devuelve la cantidad de libros insertados'''
    with open("populate.json","r",encoding="utf-8") as datos:
        libros = json.load(datos)
    insertados = 0
    for libro in libros:
        resultado = await books.update_one(
            {"isbn":libro["isbn"]},
            {"$setOnInsert": libro}, #setoninsert inserta si upsert=true, si existe Y se actualiza, no hace nada
            upsert=True
        )

        if resultado.upserted_id is not None:
            insertados += 1

    return insertados