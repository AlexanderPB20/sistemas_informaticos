from quart import Quart, jsonify
app = Quart(__name__)

@app.put('/user')
async def create_user(name: str,password: str):
    
    #Generacion del uuid
    secret_uuid = uuid.uuid4()
    stringified_uuid = str(secret_uuid)
    
    #Password hasheada
    password256 = hashlib.sha256(password).hexdigest()
    
    entry = {"uuid": secret_uuid, "username" = name, "password"=password256}
    return jsonify(entry)

@app.post('/user')
async def login(name: str, password: str):
    #Login code goes here

@app.patch('/user')
async def modify(password: str):
    #Mofify password code goes here


if __name__ == '__main__':
    app.run(host='localhost', port=5050)