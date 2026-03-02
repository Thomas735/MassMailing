#!/bin/bash
# Se placer dans le dossier où se trouve ce script
cd "$(dirname "$0")"

# Activer l'environnement virtuel et lancer le programme principal
source venv/bin/activate
python3 main.py
