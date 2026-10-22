Para comenzar la ejecución de los microservicios, en una terminal con permisos de administrador
se debe ejecutar:

docker-compose up --build -d

Para detener el servicio, simplemente ejecutando:

docker-compose down

debería detener los servicios.


Una vez hecho esto y con los servicios arrancados, se puede ejecutar el fichero de pruebas cliente.py, 
usando un entorno virtual de python con:

NOTA IMPORTANTE: Como ya cuenta con base de datos y los ids y nombres de usuario deben ser unicos
el cliente.py SÓLO FUNCIONA UNA VEZ. En caso de querer volver a ejecutarlo, es necesario cambiar las constantes
del fichero con otros valores nuevos

mkdir -p venv/si1p1
python3 -m venv venv/si1p1
source ./venv/si1p1/bin/activate
python3 cliente.py
pip install -r requirements.txt

Adicionalmete, se ha creado un script de bash de inicio que arranca todos los servicios y ejecuta las pruebas
directamente.
Se puede ejecutar con

sh ./init.sh

siempre y cuando el script tenga permisos de ejecución.