from quart import Quart, jsonify, request, Blueprint

routes_blueprint = Blueprint('routes_blueprint', __name__)

@routes_blueprint.post("auth/register")
async def register():
    return