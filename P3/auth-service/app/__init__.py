from quart import Quart, jsonify, request
from .routes import routes_blueprint

app = Quart(__name__)


# Source - https://stackoverflow.com/a/74214174
# Posted by lmiguelvargasf, modified by community. See post 'Timeline' for change history
# Retrieved 2026-11-03, License - CC BY-SA 4.0
app.register_blueprint(routes_blueprint, url_prefix='/auth')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051)

