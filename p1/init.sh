#!/bin/bash

echo "----Ejecutando dockers----"
docker-compose up --build -d

echo "----Creando entorno virtual de python----"
mkdir -p venv/si1p1
python3 -m venv venv/si1p1
source ./venv/si1p1/bin/activate
pip install -r requirements.txt

echo "----Ejecutando cliente de pruebas----"
python3 cliente.py


echo "----Deteniendo dockers---"
docker-compose down

echo "----Saliendo del entorno virtual---"
deactivate