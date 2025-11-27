import requests
import json
from config import Config


class OdooClient:
    def __init__(self):
        self.url = Config.ODOO_URL
        self.db = Config.ODOO_DB
        self.username = Config.ODOO_USERNAME
        self.password = Config.ODOO_PASSWORD
        self.uid = None
        self.session = requests.Session()
    
    def _jsonrpc(self, endpoint, params):
        """Ejecutar llamada JSON-RPC a Odoo"""
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": params,
            "id": 1
        }
        response = self.session.post(
            f"{self.url}{endpoint}",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        result = response.json()
        if "error" in result:
            raise Exception(result["error"].get("data", {}).get("message", str(result["error"])))
        return result.get("result")
    
    def authenticate(self):
        """Autenticar con Odoo y obtener UID"""
        result = self._jsonrpc("/web/session/authenticate", {
            "db": self.db,
            "login": self.username,
            "password": self.password
        })
        self.uid = result.get("uid")
        if not self.uid:
            raise Exception("Authentication failed")
        return self.uid
    
    def search_read(self, model, domain=None, fields=None, limit=None, order=None):
        """Buscar y leer registros de un modelo"""
        if not self.uid:
            self.authenticate()
        
        kwargs = {}
        if fields:
            kwargs["fields"] = fields
        if limit:
            kwargs["limit"] = limit
        if order:
            kwargs["order"] = order
        
        return self._jsonrpc("/web/dataset/call_kw", {
            "model": model,
            "method": "search_read",
            "args": [domain or []],
            "kwargs": kwargs
        })
    
    def read(self, model, ids, fields=None):
        """Leer registros específicos por ID"""
        if not self.uid:
            self.authenticate()
        
        kwargs = {}
        if fields:
            kwargs["fields"] = fields
        
        return self._jsonrpc("/web/dataset/call_kw", {
            "model": model,
            "method": "read",
            "args": [ids],
            "kwargs": kwargs
        })
    
    def call_method(self, model, method, ids=None, args=None, kwargs=None):
        """Llamar método personalizado de un modelo"""
        if not self.uid:
            self.authenticate()
        
        return self._jsonrpc("/web/dataset/call_kw", {
            "model": model,
            "method": method,
            "args": [ids] if ids else (args or []),
            "kwargs": kwargs or {}
        })


# Singleton
odoo_client = OdooClient()
