## ./app.py
```py
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from services import CMSService

app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def index():
    """Health check"""
    return jsonify({
        "status": "ok",
        "service": "Jasper CMS API",
        "version": "1.0.0"
    })


@app.route("/api/v1/page", methods=["GET"])
def get_page():
    """
    Obtener datos completos de una página
    Query params:
        - url: URL de la página (default: "/")
    """
    page_url = request.args.get("url", "/")
    
    try:
        data = CMSService.get_full_page_data(page_url)
        return jsonify({"data": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/page/meta", methods=["GET"])
def get_meta():
    """Obtener solo meta tags de una página"""
    page_url = request.args.get("url", "/")
    
    try:
        data = CMSService.get_meta_by_url(page_url)
        return jsonify({"data": {"meta": data}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/page/sections", methods=["GET"])
def get_sections():
    """Obtener solo secciones de una página"""
    page_url = request.args.get("url", "/")
    
    try:
        data = CMSService.get_sections_by_page(page_url)
        return jsonify({"data": {"sections": data}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/page/products", methods=["GET"])
def get_products():
    """Obtener solo product grid de una página"""
    page_url = request.args.get("url", "/")
    
    try:
        data = CMSService.get_product_grid_by_page(page_url)
        return jsonify({"data": {"product_grid": data}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/sections", methods=["GET"])
def get_all_sections():
    """
    Obtener todas las secciones activas
    Query params:
        - type: Filtrar por tipo (hero, feature, brand_story, etc.)
        - limit: Límite de resultados
    """
    section_type = request.args.get("type")
    limit = request.args.get("limit", type=int)
    
    try:
        from odoo_client import odoo_client
        
        domain = [("active", "=", True)]
        if section_type:
            domain.append(("section_type", "=", section_type))
        
        sections = odoo_client.search_read(
            "jasper.cms.section",
            domain=domain,
            fields=["section_id", "section_type", "layout", "content_id", "page_id"],
            order="sequence asc",
            limit=limit
        )
        
        result = []
        for section in sections:
            section_data = {
                "id": section.get("section_id", ""),
                "type": section.get("section_type", ""),
                "layout": section.get("layout", ""),
                "page": section["page_id"][1] if section.get("page_id") else None,
                "content": {}
            }
            
            content_id = section.get("content_id")
            if content_id and content_id[0]:
                content = CMSService._get_section_content(content_id[0])
                section_data["content"] = content
            
            result.append(section_data)
        
        return jsonify({"data": {"sections": result}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/v1/grids", methods=["GET"])
def get_all_grids():
    """Obtener todos los product grids activos"""
    try:
        from odoo_client import odoo_client
        
        grids = odoo_client.search_read(
            "jasper.cms.product.grid",
            domain=[("active", "=", True)],
            fields=["name", "title", "max_items", "item_ids", "page_id"],
            order="sequence asc"
        )
        
        result = []
        for grid in grids:
            items = CMSService._get_grid_items(grid.get("item_ids", []), grid.get("max_items", 8))
            result.append({
                "name": grid.get("name", ""),
                "title": grid.get("title", ""),
                "page": grid["page_id"][1] if grid.get("page_id") else None,
                "items": items
            })
        
        return jsonify({"data": {"grids": result}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )
```

## ./config.py
```py
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
```

## ./odoo_client.py
```py
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
```

## ./services/__init__.py
```py
from .cms_service import CMSService
```

## ./services/cms_service.py
```py
from odoo_client import odoo_client


class CMSService:
    
    @staticmethod
    def get_meta_by_url(page_url="/"):
        """Obtener meta tags por URL de página"""
        metas = odoo_client.search_read(
            "jasper.cms.meta",
            domain=[("page_url", "=", page_url), ("active", "=", True)],
            fields=["meta_title", "meta_description", "meta_keywords"],
            limit=1
        )
        if metas:
            meta = metas[0]
            return {
                "title": meta.get("meta_title", ""),
                "description": meta.get("meta_description", ""),
                "keywords": meta.get("meta_keywords", "")
            }
        return {"title": "", "description": "", "keywords": ""}
    
    @staticmethod
    def get_sections_by_page(page_url="/"):
        """Obtener secciones de una página"""
        pages = odoo_client.search_read(
            "jasper.cms.meta",
            domain=[("page_url", "=", page_url), ("active", "=", True)],
            fields=["id"],
            limit=1
        )
        
        if not pages:
            return []
        
        page_id = pages[0]["id"]
        
        sections = odoo_client.search_read(
            "jasper.cms.section",
            domain=[("page_id", "=", page_id), ("active", "=", True)],
            fields=["section_id", "section_type", "layout", "content_id"],
            order="sequence asc"
        )
        
        result = []
        for section in sections:
            section_data = {
                "id": section.get("section_id", ""),
                "type": section.get("section_type", ""),
                "layout": section.get("layout", ""),
                "content": {}
            }
            
            content_id = section.get("content_id")
            if content_id and content_id[0]:
                content = CMSService._get_section_content(content_id[0])
                section_data["content"] = content
            
            result.append(section_data)
        
        return result
    
    @staticmethod
    def _get_section_content(content_id):
        """Obtener contenido de una sección"""
        contents = odoo_client.read(
            "jasper.cms.section.content",
            [content_id],
            fields=[
                "background_text", "badge_text", "badge_icon",
                "subtitle", "title_normal", "title_highlight",
                "description", "cta_text", "cta_sub_text", "cta_href",
                "image_src", "image_alt", "show_badge"
            ]
        )
        
        if not contents:
            return {}
        
        c = contents[0]
        result = {}
        
        if c.get("background_text"):
            result["background_text"] = c["background_text"]
        
        if c.get("badge_text"):
            result["badge"] = {
                "text": c["badge_text"],
                "icon": c.get("badge_icon") or "star"
            }
        
        if c.get("subtitle"):
            result["subtitle"] = c["subtitle"]
        
        if c.get("title_normal") or c.get("title_highlight"):
            result["title"] = {
                "normal": c.get("title_normal") or "",
                "highlight": c.get("title_highlight") or ""
            }
        
        if c.get("description"):
            result["description"] = c["description"]
        
        if c.get("cta_text"):
            result["cta"] = {
                "text": c["cta_text"],
                "href": c.get("cta_href") or "#"
            }
            if c.get("cta_sub_text"):
                result["cta"]["sub_text"] = c["cta_sub_text"]
        
        if c.get("image_src"):
            result["image"] = {
                "src": c["image_src"],
                "alt": c.get("image_alt") or ""
            }
            if c.get("show_badge"):
                result["image"]["show_badge"] = True
        
        return result
    
    @staticmethod
    def get_product_grid_by_page(page_url="/"):
        """Obtener product grid de una página"""
        pages = odoo_client.search_read(
            "jasper.cms.meta",
            domain=[("page_url", "=", page_url), ("active", "=", True)],
            fields=["id"],
            limit=1
        )
        
        if not pages:
            return None
        
        page_id = pages[0]["id"]
        
        grids = odoo_client.search_read(
            "jasper.cms.product.grid",
            domain=[("page_id", "=", page_id), ("active", "=", True)],
            fields=["title", "max_items", "item_ids"],
            order="sequence asc",
            limit=1
        )
        
        if not grids:
            return None
        
        grid = grids[0]
        items = CMSService._get_grid_items(grid.get("item_ids", []), grid.get("max_items", 8))
        
        return {
            "title": grid.get("title", ""),
            "items": items
        }
    
    @staticmethod
    def _get_grid_items(item_ids, max_items):
        """Obtener items del product grid"""
        if not item_ids:
            return []
        
        items = odoo_client.search_read(
            "jasper.cms.product.grid.item",
            domain=[("id", "in", item_ids), ("active", "=", True)],
            fields=[
                "product_id", "manual_name", "manual_slug", "manual_price",
                "manual_currency", "manual_image_src", "manual_category",
                "is_new", "is_featured"
            ],
            order="sequence asc",
            limit=max_items
        )
        
        result = []
        for item in items:
            product_id = item.get("product_id")
            
            if product_id and product_id[0]:
                products = odoo_client.read(
                    "product.template",
                    [product_id[0]],
                    fields=["id", "name", "list_price", "categ_id"]
                )
                if products:
                    p = products[0]
                    result.append({
                        "id": p["id"],
                        "name": p["name"],
                        "slug": item.get("manual_slug") or "",
                        "price": p.get("list_price", 0),
                        "currency": item.get("manual_currency") or "USD",
                        "image": item.get("manual_image_src") or f"/web/image/product.template/{p['id']}/image_1024",
                        "category": p["categ_id"][1] if p.get("categ_id") else "",
                        "is_new": item.get("is_new", False),
                        "is_featured": item.get("is_featured", False)
                    })
            else:
                result.append({
                    "id": item["id"],
                    "name": item.get("manual_name") or "",
                    "slug": item.get("manual_slug") or "",
                    "price": item.get("manual_price", 0),
                    "currency": item.get("manual_currency") or "USD",
                    "image": item.get("manual_image_src") or "",
                    "category": item.get("manual_category") or "",
                    "is_new": item.get("is_new", False),
                    "is_featured": item.get("is_featured", False)
                })
        
        return result
    
    @staticmethod
    def get_full_page_data(page_url="/"):
        """Obtener todos los datos de una página"""
        return {
            "meta": CMSService.get_meta_by_url(page_url),
            "sections": CMSService.get_sections_by_page(page_url),
            "product_grid": CMSService.get_product_grid_by_page(page_url)
        }
```

