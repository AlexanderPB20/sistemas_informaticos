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
        return True
    return False

'''
Función que comprueba si una ruta a los archivos de un usuario (uid)
'''
def comprobar_uid(uid: str) -> bool:
    path = Path('/file/',uid)
    return path.exists()

'''
Función que lista, dado un uid, los ficheros de ese usuario. Permite listar 
los privados y públicos o sólo los públicados en base al valor de la flag "private"
No comprueba si el path con ese uid existe o no
'''
def listar_ficheros(uid : str, private = False):
    file_list = {}

    path = Path('./file/',uid,'/public/')
    files_found = [file.name for file in path.iterdir() if file.is_file()]
    file_list['public'] = files_found

    if private:
        path = Path('./file/',uid,'/private/')
        files_found = [file.name for file in path.iterdir() if file.is_file()]
        file_list['private'] = files_found
    
    return file_list


'''
Función para gestionar las peticiones GET.
Dada la ruta y un uid, lista los ficheros públicos del uid, si existe.
Se puede agregar la cabecera de autenticación con token para listar los ficheros privados
si dicho token es correcto.
'''
@app.get('/file/<uid>')
async def list_documents(uid):

    if not comprobar_uid(uid):
        return jsonify({'error':'El uid introducido no existe o no es un directorio'}),404
    
    #Comprobar si se ha añadido cabecera con token para
    #mostrar tanto los públicos como los ocultos
    authorized = False
    token = request.headers.get("Authorization")
    if token:
        token = token[7:] #Eliminar "Bearer" del string
        if validar_token(token, uid):
            #Caso en el que se tengan permisos para listar los documentos privados
            authorized = True

    #Respuesta del servidor si no tiene permisos de listar privados
    return jsonify(listar_ficheros(uid, authorized)), 200
'''
Función para gestionar las peticiones GET.
Dada la ruta, un uid y un nombre de fichero, Obtiene el contenido del fichero, si existe.
Se puede agregar la cabecera de autenticación con token para listar los ficheros privados
si dicho token es correcto.
'''
@app.get('/file/<uid>/<filename>')
async def get_content(uid, filename):
    
    if not comprobar_uid(uid):
        return jsonify({'error':'El uid introducido no existe o no es un directorio'}),404
    
    #Comprobar si se ha añadido cabecera con token para
    #buscar tanto en los públicos como los ocultos
    authorized = False
    token = request.headers.get("Authorization")
    if token:
        token = token[7:] #Eliminar "Bearer" del string
        if validar_token(token, uid):
            #Caso en el que se tengan permisos para listar los documentos privados
            authorized = True

    ficheros = listar_ficheros(uid, True)
    for visibility in ficheros:
        if filename in ficheros[visibility]:
            path = Path('/file/',uid,'/',visibility,'/',filename)
            return jsonify({'content': path.read_text()}),200

    return jsonify({'error':'Fichero no encontrado'}),404
'''
Función para gestionar las peticiones PUT.
Dada la ruta, un uid y un nombre de ficero, Cambia el contenido del fichero al recibido en el JSON adjunto.
Si el fichero no existe, lo crea con el contenido.
Es necesario autenticarse con token para hacer esta acción.
'''
@app.put('/file/<uid>/<filename>')
async def create_or_update(uid,filename):
    #TODO: falta implementar el leer el contenido del fichero a crear/cambiar desde el json introducido
    #Uid correcto?    
    if not comprobar_uid(uid):
        return jsonify({'error':'El uid introducido no existe o no es un directorio'}),404
    
    #Para subir ficheros será necesario autenticarse
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({'error':'La petición debe tener un token de autenticación en la cabecera'}), 400
    
    token = token[7:] #Eliminar "Bearer" del string
    if not validar_token(token, uid):
        return jsonify({'error': 'Autenticación fallida. Revisa el uid o el token introducidos'}), 401

    #Para crear o actualizar los ficheros se va a buscar
    #linealmente en los directorios. Primero en público, donde si lo encuentra, lo reemplaza
    #y luego en el privado, donde si no lo encuentra, lo crea
    ficheros = listar_ficheros(uid, True)
    for visibility in ficheros:
        if filename in ficheros[visibility]:
            path = Path('/file/',uid,'/',visibility,'/',filename)
            path.write_text(texto)
            return jsonify({'info': 'Recurso actualizado con éxito'}), 201
    
    #Si no encuentra el fichero, se crea en privado directamente
    path = Path('/file/',uid,'/private/',filename)
    path.touch()
    path.write_text(texto)
    return jsonify({'info',('Se ha creado un nuevo recurso ',filename,' en el directorio privado.')}),201
'''
Función para gestionar las peticiones DELETE.
Dada la ruta, un uid y un nombre de ficero, eliminará el fichero.
Es necesario autenticarse con token para hacer esta acción.
'''
@app.delete('/file/<uid>/<filename>')
async def delete(uid, filename):
    
    if not comprobar_uid(uid):
        return jsonify({'error':'El uid introducido no existe o no es un directorio'}),404
    
    #Para eliminar ficheros será necesario autenticarse
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({'error':'La petición debe tener un token de autenticación en la cabecera'}), 400
    
    token = token[7:] #Eliminar "Bearer" del string
    if not validar_token(token, uid):
        return jsonify({'error': 'Autenticación fallida. Revisa el uid o el token introducidos'}), 401

    ficheros = listar_ficheros(uid, True)
    for visibility in ficheros:
        if filename in ficheros[visibility]:
            path = Path('/file/',uid,'/',visibility,'/',filename)
            path.unlink()
            return jsonify({'info':('Fichero ',filename,' eliminado')}),200

    return jsonify({'error':'Fichero no encontrado'}),404

'''
Función para gestionar las peticiones PATCH.
Dada la ruta, un uid y un nombre de ficero, Cambia la visibilidad del fichero a pública. Esta acción es irreversible.
Es necesario autenticarse con token para hacer esta acción.
'''
@app.patch('/file/<uid>/<filename>')
async def change_visibility(uid, filename):
    
    if not comprobar_uid(uid):
        return jsonify({'error':'El uid introducido no existe o no es un directorio'}),404
    
    #Para modificar la visibilidad de ficheros será necesario autenticarse
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({'error':'La petición debe tener un token de autenticación en la cabecera'}), 400
    
    token = token[7:] #Eliminar "Bearer" del string
    if not validar_token(token, uid):
        return jsonify({'error': 'Autenticación fallida. Revisa el uid o el token introducidos'}), 401

    ficheros = listar_ficheros(uid, True)
    for visibility in ficheros:
        if filename in ficheros[visibility]:
            if visibility == 'public':
                #Nota: Decidimos contar este caso como éxito. La petición es para cambiar el fichero a público, y al gestionar
                # dicha petición, el fichero acaba (o sigue, en este caso) siéndolo.
                return jsonify({'info': 'El fichero ya es público'}), 400 
            path = Path('/file/',uid,'/private/',filename)
            path.move('/file/',uid,'/public/',filename)
            return jsonify({'info':('Fichero ',filename,' establecido como público')}),200

    return jsonify({'error':'Fichero no encontrado'}),404

if __name__ == '__main__':
    app.run(host='localhost', port=5051)
