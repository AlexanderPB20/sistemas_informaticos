from quart import Quart, jsonify, request
import uuid
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
app = Quart(__name__)


def comprobar_uid(uid: str) -> bool:
    path = Path('/file/',uid)
    return path.exists()

@app.get('/file/<uid>')
async def list_documents(uid):
    path = Path('./file/',uid)

    if not comprobar_uid(uid):
        return jsonify({'error':'El uid introducido no existe o no es un directorio'}),404
    
    file_list = [file.name for file in path.iterdir() if file.is_file()]
    return jsonify({'files': file_list}), 200

@app.put('/file/<uid>/<filename>')
async def create_or_update(uid,filename):
    #TODO contenido del fichero en el json??
    #TODO Visibilidad. Separarlo por carpetas??
    #TODO ^ revisar permisos del uid que accede? ^
    path = Path('./file/',uid,"/",filename)
    
    if not comprobar_uid(uid)
        return jsonify({'error':'El uid introducido no existe o no es un directorio'}),404

    #Comprobar si ya existe el fichero, en tal caso actualizar



if __name__ == '__main__':
    app.run(host='localhost', port=5050)
