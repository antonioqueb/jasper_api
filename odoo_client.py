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
        try:
            response = self.session.post(
                f"{self.url}{endpoint}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            raise Exception(f"Connection error to Odoo: {str(e)}")

        if "error" in result:
            err_msg = result["error"].get("data", {}).get("message", str(result["error"]))
            raise Exception(f"Odoo RPC Error: {err_msg}")
            
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
        """Buscar y leer registros"""
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
    
    def call_method(self, model, method, ids=None, args=None, kwargs=None):
        """Llamar método personalizado del modelo"""
        if not self.uid:
            self.authenticate()
        
        # args debe ser una lista. Si hay IDs, son el primer argumento.
        rpc_args = []
        if ids:
            rpc_args.append(ids)
        if args:
            rpc_args.extend(args)

        return self._jsonrpc("/web/dataset/call_kw", {
            "model": model,
            "method": method,
            "args": rpc_args,
            "kwargs": kwargs or {}
        })

# Singleton
odoo_client = OdooClient()