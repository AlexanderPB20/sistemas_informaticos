from quart import Quart, jsonify, request
import uuid
import hashlib
app = Quart(__name__)

users = {}


@app.put('/user')
async def create_user():
    #Tomado de: https://mojoauth.com/parse-and-generate-formats/parse-and-generate-json-with-quart#handling-incoming-json-requests
    datos = await request.get_json()
    if datos:
        #Generacion del uuid
        secret_uuid = uuid.uuid4()
        stringified_uuid = str(secret_uuid)
        
        #Password hasheada
        password = datos.get('password')
        password256 = hashlib.sha256(password.encode()).hexdigest()
    
        users[stringified_uuid] = {"user":datos.get('name'),
                        "password":password256}
        # curl -X PUT "http://127.0.0.1:5050/user" -H "Content-Type: application/json" -d '{"name":"felipe","password":"mypassword"}'
        
        return users, 201
    #Si no llega un json en la request
    return {'error':'No se ha recibido JSON'}, 400

@app.post('/user')
async def login(name: str):
    #Login code goes here
    return jsonify.loads(name)

@app.patch('/user')
async def modify(password: str):
    #Mofify password code goes here
    return "Hello world"

if __name__ == '__main__':
    app.run(host='localhost', port=5050)