from quart import Quart, jsonify, request
from .routes import routes_blueprint

app = Quart(__name__)


app.register_blueprint(routes_blueprint, url_prefix='/auth')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051)

