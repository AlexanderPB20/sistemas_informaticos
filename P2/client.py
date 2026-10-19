import requests

USER_URL = "http://localhost:5050"
API_URL = "http://localhost:5051"

tests_passed = 0
total_tests = 0

def test(cond, msg):
    global tests_passed, total_tests
    total_tests += 1
    if cond:
        print(f" [OK] {msg}")
        tests_passed += 1
    else:
        print(f" [FALLO] {msg}")

print("=== INICIANDO BATERIA DE PRUEBAS AUTOMATIZADA P2 ===")

# 1. Registro
r = requests.put(f"{USER_URL}/user", json={"name": "test_auto", "password": "pass", "country": "Spain"})
test(r.status_code in [201, 409], "Registro de usuario (201 o 409)")

# 2. Login
r = requests.post(f"{USER_URL}/user", json={"name": "test_auto", "password": "pass"})
test(r.status_code == 200, "Login correcto (200)")
data = r.json()
uid = data.get("uid")
token = data.get("token")
headers = {"Authorization": f"Bearer {token}"}

# 3. Recarga de saldo
r = requests.patch(f"{USER_URL}/user", headers=headers, json={"uid": uid, "balance": 50.0})
test(r.status_code == 200, "Incremento de saldo (200)")

# 4. Catalogo
r = requests.get(f"{API_URL}/film/")
test(r.status_code == 200 and len(r.json()) > 0, "Obtener catalogo de peliculas (200)")

# 5. Anadir al carrito
r = requests.put(f"{API_URL}/cart/", headers=headers, json={"uid": uid, "filmID": 1, "amount": 1})
test(r.status_code == 201, "Anadir item al carrito (201)")

# 6. Consultar carrito
r = requests.get(f"{API_URL}/cart/", headers=headers, json={"uid": uid})
test(r.status_code == 200 and len(r.json()) > 0, "Consultar carrito (200)")

# 7. Votar pelicula
r = requests.put(f"{API_URL}/vote/", headers=headers, json={"uid": uid, "filmID": 1, "score": 9})
test(r.status_code in [201, 200], "Votar pelicula entre 0 y 10 (201)")

# 8. Pagar carrito
r = requests.post(f"{API_URL}/cart/", headers=headers, json={"uid": uid})
test(r.status_code == 201, "Pagar carrito y generar compra (201)")

# 9. Ventas por ano y pais
r = requests.get(f"{API_URL}/ventas/2026/Spain")
test(r.status_code == 200 and len(r.json()) > 0, "Endpoint de ventas por ano y pais (200)")

print("\n==========================================")
print(f"RESUMEN DE PRUEBAS: {tests_passed}/{total_tests} SUPERADAS")
print("==========================================")
