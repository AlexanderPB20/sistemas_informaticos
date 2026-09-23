from quart import Quart, jsonify, request
import uuid
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
app = Quart(__name__)


if __name__ == '__main__':
    app.run(host='localhost', port=5050)


@app.get('/user/<uid>')
async def list_documents():
    datos = await request.get_json()
    if not datos:
        #Si no llega un json en la request
        return jsonify({'error':'No se ha recibido JSON'}), 400
    if not datos.get('uid'):
        #Si falta algún campo en el json
        return jsonify({'error':'El JSON recibido debe contener un campo "uid".'}), 400
    uid = datos.get('uid')
    path = Path('./files/',uid)
    if not path.exists():
        return jsonify({'error':'El uid introducido no existe'}),404
