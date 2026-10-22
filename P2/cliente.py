import requests

USER_ADDRESS = "http://127.0.0.1:5050/user"
API_ADDRESS = "http://127.0.0.1:5051/"

USER = "usuario_prueba"
PASSWORD = "password_prueba"

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
    json={"name":USER,"password":PASSWORD, "country": "Spain"})

if not probar_respuesta(201, "Usuario nuevo correcto", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

#Si el usuario existe, salir
if respuesta.status_code == 409:
    exit()

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

if not probar_respuesta(401, "Login credenciales incorrectas", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

#######################################
#   USER PATCH
#######################################

# 6. Más saldo OK
respuesta = requests.patch(
    USER_ADDRESS,
    headers = {"Authorization": f"Bearer {token}"},
    json={"uid":uid,"balance":20})

if not probar_respuesta(200, "Incremento de saldo", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

# 7. Token incorrecto ERROR
respuesta = requests.patch(
    USER_ADDRESS,
    headers={"Authorization":f"Bearer 3232132321-32-321-321-21"},
    json={"uid":uid,"balance":2})

if not probar_respuesta(401, "Token incorrecto en aumento de saldo", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1


# 8. Cabecera incompleta ERROR
respuesta = requests.patch(
    USER_ADDRESS,
    json={"uid":uid,"balance":2})

if not probar_respuesta(400, "Cabecera incompleta", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1


#######################################
#   FILM GET
#######################################

# 9. Listar peliculas OK
respuesta = requests.get(
    f"{API_ADDRESS}/film")

if not probar_respuesta(200, "Listar peliculas", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

print("ID\tTitulo\t\t\tUnidades\tPuntuacion")
for film in respuesta.json():
    print(f"{film["filmID"]}\t{film["title"]}\t{film["amount"]}\t{film["filmScore"]}")
# 10. Listar peliculas por nombre OK
respuesta = requests.get(
    f"{API_ADDRESS}/film/Immortal")

if not probar_respuesta(200, "Filtrar peliculas por nombre", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

# 11. Listar carrito del usuario OK
respuesta = requests.get(
    f"{API_ADDRESS}/cart",
    headers={"Authorization":f"Bearer {token}"},
    json={"uid":uid})

if not probar_respuesta(200, "Listar carrito", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1


# 12. Listar carrito del usuario ERROR cabecera incompleta
respuesta = requests.get(
    f"{API_ADDRESS}/cart",
    json={"uid":uid})

if not probar_respuesta(403, "Listar carrito sin token", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

#######################################
#   FILM PUT
#######################################

# 13. Agregar pelicula a la base de datos OK
respuesta = requests.put(
    f"{API_ADDRESS}/film",
    headers={"Authorization":f"Bearer {token}"},
    json={"uid":uid, "title":"Requiem aeternam",
          "description":"Dona eis, Domine. Libera me, Domine, de morte aeterna.",
          "directorID":1,
          "amount":3,
          "price":10.99})

if not probar_respuesta(201, "Agregar nueva película", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

filmid = respuesta.json()['filmID']

# 14. Agregar pelicula al carrito OK
respuesta = requests.put(
    f"{API_ADDRESS}/cart",
    headers={"Authorization":f"Bearer {token}"},
    json={"uid":uid, "filmID": filmid,
          "amount":1})

if not probar_respuesta(201, "Meter película en el carrito", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

respuesta = requests.get(
    f"{API_ADDRESS}/cart",
    headers={"Authorization":f"Bearer {token}"},
    json={"uid":uid})
print(respuesta.json())

# 15. Voto OK
respuesta = requests.put(
    f"{API_ADDRESS}/vote",
    headers={"Authorization":f"Bearer {token}"},
    json={"uid":uid, "filmID": filmid,
          "score":10})

if not probar_respuesta(201, "Votar una película", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

#######################################
#   FILM POST
#######################################
# 16. Pagar carrito OK

respuesta = requests.post(
    f"{API_ADDRESS}/cart",
    headers={"Authorization":f"Bearer {token}"},
    json={"uid":uid})

if not probar_respuesta(201, "Pagar el carrito", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

#######################################
#   FILM DELETE
#######################################
# 17. Eliminar una pelicula del carrito OK
respuesta = requests.put(
    f"{API_ADDRESS}/cart",
    headers={"Authorization":f"Bearer {token}"},
    json={"uid":uid, "filmID": filmid,
          "amount":1})

respuesta = requests.delete(
    f"{API_ADDRESS}/cart",
    headers={"Authorization":f"Bearer {token}"},
    json={"uid":uid, "filmID": filmid})
if not probar_respuesta(201, "Eliminar linea del carrito", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

# 18. Eliminar una pelicula OK
respuesta = requests.delete(
    f"{API_ADDRESS}/film",
    headers={"Authorization":f"Bearer {token}"},
    json={"uid":uid, "filmID": filmid})
if not probar_respuesta(201, "Eliminar pelicula", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1

# 19. Sacar ventas del año
respuesta = requests.get(
    f"{API_ADDRESS}/ventas/2026/Spain",
    headers={"Authorization":f"Bearer {token}"})
if not probar_respuesta(200, "Ventas", respuesta.status_code, respuesta.json()):
    not_passed+=1
else:
    passed += 1
print("##################################")
print(f"Resumen de pruebas: {passed}/{passed+not_passed} SUPERADAS")
print("##################################")