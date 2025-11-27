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
