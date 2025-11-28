from odoo_client import odoo_client
from config import Config

class CMSService:
    
    @staticmethod
    def _fix_url(url):
        """
        Convierte rutas relativas (/web/image...) en absolutas públicas.
        """
        if not url:
            return ""

        public_base = getattr(Config, 'ODOO_PUBLIC_URL', Config.ODOO_URL).rstrip('/')
        
        # Si ya tiene http, verificamos si es la URL interna y la cambiamos por la pública
        if url.startswith("http"):
            internal_base = Config.ODOO_URL.rstrip('/')
            if internal_base in url and public_base != internal_base:
                return url.replace(internal_base, public_base)
            return url
            
        # Si es relativa, pegamos el dominio público
        clean_path = url.lstrip('/')
        return f"{public_base}/{clean_path}"

    @staticmethod
    def _traverse_and_fix_images(data):
        """
        Recorre recursivamente el JSON (dict o list) buscando claves
        'image', 'src' o 'meta_image' para arreglar las URLs.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if key in ['src', 'image'] and isinstance(value, str):
                    data[key] = CMSService._fix_url(value)
                elif key == 'image' and isinstance(value, dict):
                    # Caso: image: { src: "..." }
                    CMSService._traverse_and_fix_images(value)
                else:
                    CMSService._traverse_and_fix_images(value)
        elif isinstance(data, list):
            for item in data:
                CMSService._traverse_and_fix_images(item)
        return data

    @staticmethod
    def get_home_content():
        """
        Obtiene la configuración del Home.
        1. Busca el ID del registro jasper.home.
        2. Llama al método 'get_home_data' de Odoo.
        3. Procesa las URLs de las imágenes.
        """
        # 1. Buscar el registro único
        records = odoo_client.search_read(
            "jasper.home",
            domain=[], # Trae todo (debería ser solo 1)
            fields=['id'],
            limit=1
        )
        
        if not records:
            raise Exception("No Home Page configuration found in Odoo.")
            
        home_id = records[0]['id']
        
        # 2. Llamar al método del modelo que ya estructura el JSON
        # Esto nos evita duplicar la lógica de mapeo de campos aquí
        raw_data = odoo_client.call_method(
            "jasper.home",
            "get_home_data",
            ids=[home_id]
        )
        
        # 3. Hidratar URLs (Odoo devuelve relativas, Flask las hace absolutas)
        final_data = CMSService._traverse_and_fix_images(raw_data)
        
        return final_data