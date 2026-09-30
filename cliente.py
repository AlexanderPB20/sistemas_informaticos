import requests

USER_ADDRESS = "http://127.0.0.1:5050/user"
FILE_ADDRESS = "http://127.0.0.1:5051/file"

USER = "Usuario_prueba"
PASSWORD = "password_prueba"
NEW_PASWORD = "password_nueva"


test = 1
def probar_respuesta(codigo_esperado, nombre_test, codigo_obtenido, mensaje_servidor):
    global test
    ret_value = True
    
    print("________________________________")
    print(f"TEST {test}: {nombre_test}")
    print("Probando respuesta de servidor.\n\n")

    if codigo_esperado != codigo_obtenido:
        print("ERROR: el código obtenido por el servidor no es el esperado.")
        print(f"Esperado: {codigo_esperado}\nObtenido: {codigo_obtenido}")
        ret_value = False
    else:
        print(f"OK: recibido código esperado.\nCódigo {codigo_esperado}")
    
    print(f"Respuesta del servidor:\n{mensaje_servidor}")
    print("________________________________")
    
    test += 1
    return ret_value



#######################################
#   USER PUT
#######################################
# 1. Creación de usuario OK
respuesta = requests.put(
    USER_ADDRESS,
    json={"name":USER,"password":PASSWORD})

if not probar_respuesta(201, "Usuario nuevo correcto", respuesta.status_code, respuesta.json()):
    exit

uid = respuesta.json()['uid']
token = respuesta.json()['token']


# 2. Creacion de usuario ERROR no json
respuesta = requests.put(
    USER_ADDRESS)

if not probar_respuesta(400, "Usuario nuevo no json", respuesta.status_code, respuesta.json()):
    exit


# 3. Creación de usuario ERROR json mal formulado
respuesta = requests.put(
    USER_ADDRESS,
    json={"malformado":"malformado"})

if not probar_respuesta(400, "Usuario nuevo json mal formulado", respuesta.status_code, respuesta.json()):
    exit

#######################################
#   USER POST
#######################################
# 4. Login OK
respuesta = requests.post(
    USER_ADDRESS,
    json={"name":USER, "password":PASSWORD})

if not probar_respuesta(200, "Login correcto", respuesta.status_code, respuesta.json()):
    exit

# 5. Login ERROR datos incorrectos
respuesta = requests.post(
    USER_ADDRESS,
    json={"name":"notfound", "password":"fakepassword"})

if not probar_respuesta(404, "Login credenciales incorrectas", respuesta.status_code, respuesta.json()):
    exit

#######################################
#   USER PATCH
#######################################

# 6. Cambio de contraseña OK
respuesta = requests.patch(
    USER_ADDRESS,
    headers = {"Authorization": f"Bearer {token}"},
    json={"password":NEW_PASWORD})

if not probar_respuesta(200, "Cambio de contraseña", respuesta.status_code, respuesta.json()):
    exit

# 7. Cambio de contraseña efectivo OK
respuesta = requests.post(
    USER_ADDRESS,
    json={"name":USER, "password":NEW_PASWORD})

if not probar_respuesta(200, "Login correcto tras cambio de contraseña", respuesta.status_code, respuesta.json()):
    exit

# 8. Token incorrecto ERROR
respuesta = requests.patch(
    USER_ADDRESS,
    headers={"Authorization":f"Bearer 3232132321-32-321-321-21"},
    json={"password":PASSWORD})

if not probar_respuesta(400, "Token incorrecto en cambio de contraseña", respuesta.status_code, respuesta.json()):
    exit


# 9. Cabecera incompleta ERROR
respuesta = requests.patch(
    USER_ADDRESS,
    json={"password":PASSWORD})

if not probar_respuesta(400, "Cabecera incompleta", respuesta.status_code, respuesta.json()):
    exit


#######################################
#   FILE PATCH
#######################################

