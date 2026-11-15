from quart import Quart, jsonify, request, Blueprint, Response
import mongodb_client

routes_blueprint = Blueprint('routes_blueprint', __name__)

@routes_blueprint.post("library/books")
async def create_book():
    raise NotImplementedError


@routes_blueprint.delete("library/books/<isbn>")
async def delete_book(isbn: str):
    raise NotImplementedError


@routes_blueprint.get("library/books/<isbn>")
async def get_book_details(isbn: str):
    raise NotImplementedError


@routes_blueprint.get("library/loans/active")
async def list_loans():
    raise NotImplementedError


@routes_blueprint.get("library/loans/history")
async def list_history():
    raise NotImplementedError


@routes_blueprint.get("library/books/out-of-stock")
async def list_oos():
    raise NotImplementedError


@routes_blueprint.post("library/books/<isbn>/borrow")
async def borrow_book(isbn: str):
    raise NotImplementedError


@routes_blueprint.post("library/books/<isbn>/return")
async def return_book(isbn: str):
    raise NotImplementedError