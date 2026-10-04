Para comenzar la ejecución de los microservicios, en una terminal con permisos de administrador
se debe ejecutar:

docker-compose up --build -d

Una vez hecho esto, se puede ejecutar el fichero de pruebas cliente.py con:

python3 cliente.py
ó
python cliente.py

dependiendo del sistema operativo.


Para detener el servicio, simplemente ejecutando:

docker-compose down

debería detener los servicios.



Adicionalmete, se ha creado un script de bash de inicio que arranca todos los servicios y ejecuta las pruebas
directamente.
Se puede ejecutar con

./init.sh

siempre y cuando el script tenga permisos de ejecución.