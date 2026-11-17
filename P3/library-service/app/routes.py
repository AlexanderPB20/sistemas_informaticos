from quart import Quart, jsonify, request, Blueprint, Response
from . import mongodb_client

routes_blueprint = Blueprint('routes_blueprint', __name__)

@routes_blueprint.post("library/books")
async def create_book():
    datos = await request.get_json()
    if not datos:
        return jsonify({'error':'''La petición no contiene JSON. Debe contener los siguientes campos:\n
 - isbn: (string)\n - title: (string)\n - author: (string)\n - year: (int)\n - publisher: (string)\n - stock: (int)'''}),400

    campos = ["isbn", "title", "author", "year", "publisher", "stock"]
    for campo in campos:
        if campo not in datos:
            return jsonify({'error':f'El JSON no contiene el campo "{campo}".'}), 400

    if datos["stock"] < 0:
        return jsonify({'error':'El campo "stock" no puede contener un número inferior a 0.'}), 400

    resultado = await mongodb_client.insertar_libro(
        datos.get("isbn"),
        datos.get("title"),
        datos.get("author"),
        datos.get("year"),
        datos.get("publisher"),
        datos.get("stock")
    )

    if resultado is None:
        return jsonify({'error':'Error al insertar el libro.'}), 300
    return jsonify({'info':'Libro añadido correctamente.','book':resultado}), 201


@routes_blueprint.delete("library/books/<isbn>")
async def delete_book(isbn: str):
    datos = await request.get_json()
    if not datos:
        return jsonify({'error':'La petición no contiene JSON. Debe contener los siguientes campos:\n - isbn: (string)\n'}),400

    if "isbn" not in datos:
        return jsonify({'error':'El JSON no contiene el campo "isbn".'}), 400
    
    resultado = await mongodb_client.eliminar_libro(datos.get("isbn"))
    
    if resultado == -1:
            return jsonify({'error':'ISBN no encontrado.'}), 404
    if resultado == 0:
            return jsonify({'error':'No se pudo eliminar. Libro con devoluciones pendientes.'}), 409
    return jsonify({'info':'Libro eliminado correctamente.','book':resultado}), 201


@routes_blueprint.get("library/books/<isbn>")
async def get_book_details(isbn: str):

    resultado = await mongodb_client.buscar_libro(isbn)
    
    if resultado is None:
            return jsonify({'error':'ISBN no encontrado.'}), 404
    
    return jsonify({'book':resultado}), 200

    

@routes_blueprint.get("library/loans/active")
async def list_loans():
    user_id = request.headers.get("X-User-Id")

    resultado = await mongodb_client.listar_prestamos(user_id)

    return jsonify({"active_loans":resultado}),200


@routes_blueprint.get("library/loans/history")
async def list_history():
    user_id = request.headers.get("X-User-Id")

    resultado = await mongodb_client.listar_historial(user_id)

    return jsonify({"history":resultado}), 200


@routes_blueprint.get("library/books/out-of-stock")
async def list_oos():
    resultado = await mongodb_client.listar_sin_stock()

    return jsonify({"books":resultado}),200


@routes_blueprint.post("library/books/<isbn>/borrow")
async def borrow_book(isbn: str):
    user_id = request.headers.get("X-User-Id")

    resultado = await mongodb_client.iniciar_prestamo(isbn, user_id)

    if resultado is None:
        resultado = await mongodb_client.buscar_libro(isbn)
        if resultado is None:
            return jsonify({"error":"Libro no encontrado"}), 404
        return jsonify({"error":"El libro no tiene stock"}),409

    return jsonify({"info":"Préstamo comenzado con éxito","book":resultado}),200

@routes_blueprint.post("library/books/<isbn>/return")
async def return_book(isbn: str):
    user_id = request.headers.get("X-User-Id")
    
    resultado = await mongodb_client.finalizar_prestamo(isbn, user_id)

    if resultado is None:
        return jsonify({"error":"Libro no encontrado"}), 404
        
    return jsonify({"info":"Préstamo finalizado con éxito","book":resultado}),200
    