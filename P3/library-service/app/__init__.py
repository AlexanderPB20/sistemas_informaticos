from quart import Quart, jsonify, request
from .routes import routes_blueprint
from . import mongodb_client
app = Quart(__name__)


app.register_blueprint(routes_blueprint)

@app.before_serving
async def populate():
    resultado = await mongodb_client.populate()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051)

