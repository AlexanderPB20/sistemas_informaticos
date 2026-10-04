#!/bin/bash

echo "---Ejecutando dockers---"
yes | docker-compose up --build -d

echo "----Ejecutando cliente de pruebas---"
python3 cliente.py