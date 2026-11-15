from pymongo import AsyncMongoClient as mongo

uri = "mongodb://alumnodb:1234@mongo:27017/?authSource=admin"

cliente = mongo(uri)

db = cliente["si1"]

books = db["books"]

'''
Inserta un libro con los parametros introducidos

Devuelve el nuevo id del libro insertado
'''
async def insertar_libro(isbn: str, title: str, author: str, year: int, publisher: str, stock: int):
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

    return resultado

'''
Busca un libro con isbn introducido en la base de datos

Devuelve el libro o None si no se encuentra
'''
async def buscar_libro(isbn: str):
    resultado = await books.find_one({"isbn":isbn})

    return resultado

'''
Lista todos los libros de la base de datos

Devuelve una lista con todas las entradas encontradas.
'''
async def listar_libros():
    resultado = await books.find()

    return resultado.to_list()

'''
Lista todos los libros fuera de stock

Devuelve una lista con todas las entradas encontradas.
'''
async def listar_sin_stock():
    resultado = await books.find({"available_stock":0})

    return resultado.to_list()

'''
Elimina un libro de la base de datos, si no tiene devoluciones pendientes

Devuelve -1 en caso de no encontrar el libro o no poder realizar el eliminado
Devuelve 0 en caso de que hayan devoluciones pendientes
Devuelve un objeto DeleteResult de pymongo en caso de éxito
'''
async def eliminar_libro(isbn: str):
    resultado = await buscar_libro(isbn)

    if resultado is None:
        return -1

    for loan in resultado["loan_history"]:
        if loan["return_date"] is None:
            return 0

    resultado = await books.delete_one({"isbn":isbn})
    if resultado is None:
        return -1

    return resultado

'''
Lista todos los libros pendientes de devolver por el usuario especificado

Devuelve una lista con todas las entradas encontradas
'''
async def listar_prestamos(user_id: str):
    #https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/query/specify-query/#array-operators
    resultado = books.find({
        "loan_history": {"$elemMatch": 
            {
                "user_id": user_id,
                "return_date": None
            }
        }
    })

    return resultado.to_list()

'''
Lista el historial de préstamos (devueltos) del usuario especificado

Devuelve una lista con todas las entradas encontradas
'''
async def listar_historial(user_id: str):
    resultado = books.find({
        "loan_history": {"$elemMatch":
            {
                "user_id":user_id,
                "return_date": {"$not": None}
            }
        }
    })

    return resultado.to_list()