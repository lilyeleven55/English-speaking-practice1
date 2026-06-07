@echo off
set FLASK_APP=app.py
set FLASK_DEBUG=true
python -m flask run --host=127.0.0.1 --port=5000