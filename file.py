from quart import Quart, jsonify, request
import uuid
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
app = Quart(__name__)

with open("server_secret.txt") as file:
    server_secret = next(file).strip()


'''
Función comprueba que un token coincide con un uid.
Devuelve true si coincide o false si no.
El token debe ser solo la cadena con el mismo (sin incluir "bearer")
'''
def validar_token(token, uid) -> bool:
    hashed_token = uuid.uuid5(server_secret, uid)
    if hashed_token == token:
        return true
    return false

def comprobar_uid(uid: str) -> bool:
    path = Path('/file/',uid)
    return path.exists()

def listar_ficheros(uid : str, private = false):
    file_list = {}

    path = Path('./file/',uid,'/public/')
    files_found = [file.name for file in path.iterdir() if file.is_file()]
    file_list['public'] = files_found

    if private:
        path = Path('./file/',uid,'/private/')
        files_found = [file.name for file in path.iterdir() if file.is_file()]
        file_list['private'] = files_found
    
    return file_list


@app.get('/file/<uid>')
async def list_documents(uid):

    if not comprobar_uid(uid):
        return jsonify({'error':'El uid introducido no existe o no es un directorio'}),404
    
    #Comprobar si se ha añadido cabecera con token para
    #mostrar tanto los públicos como los ocultos
    authorized = false
    token = request.headers.get("Authorization")
    if token:
        token = token[7:] #Eliminar "Bearer" del string
        if validar_token(token, uid):
            #Caso en el que se tengan permisos para listar los documentos privados
            authorized = true

    #Respuesta del servidor si no tiene permisos de listar privados
    return jsonify(listar_ficheros(uid, authorized)), 200

@app.put('/file/<uid>/<filename>')
async def create_or_update(uid,filename):
    #TODO: falta implementar el leer el contenido del fichero a crear/cambiar desde el json introducido
    #Uid correcto?    
    if not comprobar_uid(uid)
        return jsonify({'error':'El uid introducido no existe o no es un directorio'}),404
    
    #Para subir ficheros será necesario autenticarse
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({'error':'La petición debe tener un token de autenticación en la cabecera'}), 400
    
    token = token[7:] #Eliminar "Bearer" del string
    if not validar_token(token, uid)
        return jsonify({'error': 'Autenticación fallida. Revisa el uid o el token introducidos'}), 401

    #Para crear o actualizar los ficheros se va a buscar
    #linealmente en los directorios. Primero en público, donde si lo encuentra, lo reemplaza
    #y luego en el privado, donde si no lo encuentra, lo crea
    ficheros = listar_ficheros(uid, true)
    for visibility in ficheros:
        if filename in ficheros[visibility]:
            path = Path('/file/',uid,'/',visibility,'/',filename)
            path.write_text(texto)
            return jsonify('info': 'Recurso actualizado con éxito'), 201
    
    #Si no encuentra el fichero, se crea en privado directamente
    path = Path('/file/',uid,'/private/',filename)
    path.touch()
    path.write_text(texto)
    return jsonify('info',('Se ha creado un nuevo recurso ',filename,' en el directorio privado.'),201)

if __name__ == '__main__':
    app.run(host='localhost', port=5050)
