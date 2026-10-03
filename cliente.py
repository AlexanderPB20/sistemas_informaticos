import requests

USER_ADDRESS = "http://127.0.0.1:5050/user"
FILE_ADDRESS = "http://127.0.0.1:5051/file"

USER = "Usuario_prueba"
PASSWORD = "password_prueba"
NEW_PASWORD = "password_nueva"
FILENAME = "ejemplo1.txt"
FILE_CONTENT = "En un lugar de la Mancha cuyo nombre no quiero acordarme"
NEW_FILE_CONTENT = "Lorem ipsum dolor sit amet"

passed = 0
not_passed = 0
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
    not_passed+=1
else:
    passed += 1

uid = respuesta.json()['uid']
token = respuesta.json()['token']


# 2. Creacion de usuario ERROR no json
respuesta = requests.put(
    USER_ADDRESS)

if not probar_respuesta(400, "Usuario nuevo no json", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1


# 3. Creación de usuario ERROR json mal formulado
respuesta = requests.put(
    USER_ADDRESS,
    json={"malformado":"malformado"})

if not probar_respuesta(400, "Usuario nuevo json mal formulado", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

#######################################
#   USER POST
#######################################
# 4. Login OK
respuesta = requests.post(
    USER_ADDRESS,
    json={"name":USER, "password":PASSWORD})

if not probar_respuesta(200, "Login correcto", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

# 5. Login ERROR datos incorrectos
respuesta = requests.post(
    USER_ADDRESS,
    json={"name":"notfound", "password":"fakepassword"})

if not probar_respuesta(404, "Login credenciales incorrectas", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

#######################################
#   USER PATCH
#######################################

# 6. Cambio de contraseña OK
respuesta = requests.patch(
    USER_ADDRESS,
    headers = {"Authorization": f"Bearer {token}"},
    json={"password":NEW_PASWORD})

if not probar_respuesta(200, "Cambio de contraseña", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

# 7. Cambio de contraseña efectivo OK
respuesta = requests.post(
    USER_ADDRESS,
    json={"name":USER, "password":NEW_PASWORD})

if not probar_respuesta(200, "Login correcto tras cambio de contraseña", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

# 8. Token incorrecto ERROR
respuesta = requests.patch(
    USER_ADDRESS,
    headers={"Authorization":f"Bearer 3232132321-32-321-321-21"},
    json={"password":PASSWORD})

if not probar_respuesta(400, "Token incorrecto en cambio de contraseña", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1


# 9. Cabecera incompleta ERROR
respuesta = requests.patch(
    USER_ADDRESS,
    json={"password":PASSWORD})

if not probar_respuesta(400, "Cabecera incompleta", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1


#######################################
#   FILE PUT
#######################################

# 10. Crear fichero OK
respuesta = requests.put(
    f"{FILE_ADDRESS}/{uid}/{FILENAME}",
    headers={"authorization":f"Bearer {token}"},
    json={"content":FILE_CONTENT})

if not probar_respuesta(201, "Crear fichero correcto", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

# 11. Actualizar contenido de fichero OK
respuesta = requests.put(
    f"{FILE_ADDRESS}/{uid}/{FILENAME}",
    headers={"authorization":f"Bearer {token}"},
    json={"content":NEW_FILE_CONTENT})

if not probar_respuesta(201, "Actualizar contenido correcto", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

# 12. Crear fichero ERROR no content
respuesta = requests.put(
    f"{FILE_ADDRESS}/{uid}/{FILENAME}",
    headers={"authorization":f"Bearer {token}"},
    json={"malaCabecera":FILE_CONTENT})

if not probar_respuesta(400, "Crear fichero cabecera erronea", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

# 13. Crear fichero ERROR sin autenticar
respuesta = requests.put(
    f"{FILE_ADDRESS}/{uid}/{FILENAME}",
    json={"content":FILE_CONTENT})

if not probar_respuesta(400, "Crear fichero sin autenticacion", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

# 14. Crear fichero ERROR token incorrecto
respuesta = requests.put(
    f"{FILE_ADDRESS}/{uid}/{FILENAME}",
    headers={"authorization":f"Bearer 123123-123123"},
    json={"content":FILE_CONTENT})
'''
TODO: modificar file.py para admitir tokens mal formados
if not probar_respuesta(403, "Crear fichero autenticacion incorrecta", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1
'''

# 15. Crear fichero ERROR uid incorrecto
respuesta = requests.put(
    f"{FILE_ADDRESS}/nombrefalso/{FILENAME}",
    headers={"authorization":f"Bearer {token}"},
    json={"content":FILE_CONTENT})

if not probar_respuesta(403, "Crear fichero nombre erroneo", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

#######################################
#   FILE PATCH
#######################################

# 16. Cambiar visibilidad a un fichero OK

respuesta = requests.patch(
    f"{FILE_ADDRESS}/{uid}/{FILENAME}",
    headers={"authorization":f"Bearer {token}"}
    )

if not probar_respuesta(200, "Cambiar fichero a público", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

# 17. Cambiar visibilidad a un fichero que ya es público OK

respuesta = requests.patch(
    f"{FILE_ADDRESS}/{uid}/{FILENAME}",
    headers={"authorization":f"Bearer {token}"}
    )

if not probar_respuesta(200, "Cambiar fichero público de nuevo a público", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

# 18. Cambiar visibilidad a un fichero ERROR fichero inexistente

respuesta = requests.patch(
    f"{FILE_ADDRESS}/{uid}/ficheroquenoesta.txt",
    headers={"authorization":f"Bearer {token}"}
    )

if not probar_respuesta(404, "Cambiar fichero inexistente a público", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

# 19. Cambiar visibilidad a un fichero cuyo nombre ya existía en público ERROR
# Fichero nuevo en privado
respuesta = requests.put(
    f"{FILE_ADDRESS}/{uid}/{FILENAME}",
    headers={"authorization":f"Bearer {token}"},
    json={"content":NEW_FILE_CONTENT})
# Cambio este nuevo a público
respuesta = requests.patch(
    f"{FILE_ADDRESS}/{uid}/{FILENAME}",
    headers={"authorization":f"Bearer {token}"}
    )

if not probar_respuesta(200, "Cambiar fichero a público con uno ya existente con el mismo nombre", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1


print("##################################")
print(f"Resumen de pruebas: {passed}/{passed+not_passed} SUPERADAS")
print("##################################")