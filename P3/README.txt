Si el usuario tiene permiso para ejecutar los docker, sencillamente hay que
posicionarse en la carpeta de P3, donde el fichero docker-compose.yml es visible y ejecutar
en una terminal:

```
docker compose up --build
```

En ese momento, se levantarán todos los contenedores necesarios para que funcione el sistema y se pasará
la vista de la consola a la de los microservicios (unida). Puedes abandonar esta vista pulsando `d` o 
incluyendo en el inicio la opción `-d`.

Para finalizar la ejecución tan solo debe ejecutar

```
docker compose down 
```
Si desea eliminar los volúmenes y los datos, añada las opciones `--v` y `--remove-orphans` a este 
último comando.
----------------------------------------------------------------------------------------------------


En caso de no poseer permisos, deberá establecer los permisos de ejecución de docker con la siguiente 
secuencia:
```
sudo /usr/local/bin/si2setuid.sh 3000000:100000 $USER
dockerd-rootless-setuptool.sh install --skip-iptables
export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock
```


- Jorge Calle Rodríguez