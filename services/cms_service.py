from odoo_client import odoo_client
from config import Config
import sys

class CMSService:
    
    @staticmethod
    def _fix_image_url(url):
        """
        Convierte rutas relativas de Odoo en URLs absolutas.
        Ej: /web/image... -> http://midominio:8069/web/image...
        """
        if not url:
            return ""
        if url.startswith("http"):
            return url
        # Elimina barra inicial si existe para evitar doble //
        clean_path = url.lstrip('/')
        # Asegura que ODOO_URL no tenga barra final
        base_url = Config.ODOO_URL.rstrip('/')
        return f"{base_url}/{clean_path}"

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
        
        # IMPORTANTE: Pedimos 'image' explícitamente a Odoo
        contents = odoo_client.read(
            "jasper.cms.section.content",
            [content_id],
            fields=[
                "background_text", "badge_text", "badge_icon",
                "subtitle", "title_normal", "title_highlight",
                "description", "cta_text", "cta_sub_text", "cta_href",
                "image_src", "image_alt", "show_badge", "image"
            ]
        )
        
        if not contents:
            return {}
        
        c = contents[0]
        result = {}
        
        # --- DEBUG PRINTS (Aparecerán en los logs de Docker) ---
        print(f"\n[DEBUG] === Procesando Sección Content ID: {content_id} ===", flush=True)
        print(f"[DEBUG] Campo 'image' existe en respuesta Odoo? {'image' in c}", flush=True)
        
        # Odoo devuelve False si el binario está vacío, o un string base64 largo si hay imagen
        has_binary_image = bool(c.get("image"))
        print(f"[DEBUG] ¿Tiene imagen BINARIA subida? {has_binary_image}", flush=True)
        print(f"[DEBUG] Valor de texto 'image_src': {c.get('image_src')}", flush=True)
        # -------------------------------------------------------

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
        
        # --- LÓGICA DE PRIORIDAD DE IMAGEN ---
        final_src = ""
        
        # 1. Prioridad Máxima: ¿Existe una imagen binaria subida?
        if c.get("image"):
            # Generamos la URL dinámica apuntando a Odoo
            raw_src = f"/web/image?model=jasper.cms.section.content&id={content_id}&field=image"
            final_src = CMSService._fix_image_url(raw_src)
            print(f"[DEBUG] -> DECISIÓN: Usando imagen BINARIA generada: {final_src}", flush=True)
            
        # 2. Si no hay imagen subida, usamos el texto del XML
        elif c.get("image_src"):
             final_src = CMSService._fix_image_url(c["image_src"])
             print(f"[DEBUG] -> DECISIÓN: Usando imagen TEXTO (XML/Default): {final_src}", flush=True)
             
        else:
             print("[DEBUG] -> DECISIÓN: No hay imagen", flush=True)

        result["image"] = {
            "src": final_src,
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
        
        # Pedimos 'manual_image' explícitamente
        items = odoo_client.search_read(
            "jasper.cms.product.grid.item",
            domain=[("id", "in", item_ids), ("active", "=", True)],
            fields=[
                "product_id", "manual_name", "manual_slug", "manual_price",
                "manual_currency", "manual_image_src", "manual_category",
                "manual_image", "is_new", "is_featured"
            ],
            order="sequence asc",
            limit=max_items
        )
        
        result = []
        for item in items:
            product_id = item.get("product_id")
            image_url = ""
            
            # Debug simple para items
            has_manual_img = bool(item.get("manual_image"))
            # print(f"[DEBUG] Grid Item {item['id']} tiene imagen manual? {has_manual_img}", flush=True)
            
            # --- LÓGICA DE PRIORIDAD GRID ---
            
            # A. Si hay producto vinculado
            if product_id and product_id[0]:
                products = odoo_client.read(
                    "product.template",
                    [product_id[0]],
                    fields=["id", "name", "list_price", "categ_id"]
                )
                if products:
                    p = products[0]
                    
                    # 1. Override manual binario
                    if item.get("manual_image"):
                        raw_src = f"/web/image?model=jasper.cms.product.grid.item&id={item['id']}&field=manual_image"
                    # 2. Override manual texto
                    elif item.get("manual_image_src"):
                        raw_src = item["manual_image_src"]
                    # 3. Imagen producto
                    else:
                        raw_src = f"/web/image/product.template/{p['id']}/image_1024"
                    
                    image_url = CMSService._fix_image_url(raw_src)

                    result.append({
                        "id": p["id"],
                        "name": p["name"],
                        "slug": item.get("manual_slug") or "",
                        "price": p.get("list_price", 0),
                        "currency": item.get("manual_currency") or "USD",
                        "image": image_url,
                        "category": p["categ_id"][1] if p.get("categ_id") else "",
                        "is_new": item.get("is_new", False),
                        "is_featured": item.get("is_featured", False)
                    })
            
            # B. Si es item manual puro
            else:
                # 1. Imagen manual binaria
                if item.get("manual_image"):
                    raw_src = f"/web/image?model=jasper.cms.product.grid.item&id={item['id']}&field=manual_image"
                # 2. Imagen manual texto
                else:
                    raw_src = item.get("manual_image_src") or ""
                
                image_url = CMSService._fix_image_url(raw_src)

                result.append({
                    "id": item["id"],
                    "name": item.get("manual_name") or "",
                    "slug": item.get("manual_slug") or "",
                    "price": item.get("manual_price", 0),
                    "currency": item.get("manual_currency") or "USD",
                    "image": image_url,
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