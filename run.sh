#!/bin/bash
cd "$(dirname "$0")"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

pip install -r requirements.txt -q

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  Creado .env desde .env.example - configura las variables"
fi

python app.py
