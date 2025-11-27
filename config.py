import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
    ODOO_DB = os.getenv('ODOO_DB', 'odoo_db')
    ODOO_USERNAME = os.getenv('ODOO_USERNAME', 'admin')
    ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'admin')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
