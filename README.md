# Jasper CMS API

API Flask para consumir datos del módulo Jasper CMS de Odoo.

## Instalación

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Editar .env con credenciales Odoo
```

## Ejecutar

```bash
./run.sh
```

## Endpoints

| Endpoint | Descripción |
|----------|-------------|
| GET /api/v1/page?url=/ | Datos completos de página |
| GET /api/v1/page/meta?url=/ | Solo meta tags |
| GET /api/v1/page/sections?url=/ | Solo secciones |
| GET /api/v1/page/products?url=/ | Solo product grid |
| GET /api/v1/sections?type=hero&limit=5 | Todas las secciones |
| GET /api/v1/grids | Todos los product grids |

## Response Example

```json
{
  "data": {
    "meta": {
      "title": "Home - Jasper",
      "description": "Luxury stones and crystals.",
      "keywords": ""
    },
    "sections": [
      {
        "id": "hero-section-01",
        "type": "hero",
        "layout": "image_left",
        "content": {
          "background_text": "JASPER",
          "badge": {"text": "New Arrival", "icon": "star"},
          "subtitle": "The November Edit",
          "title": {"normal": "Polished", "highlight": "Landscape Jasper."},
          "description": "Sculpture of polished Landscape Jasper...",
          "cta": {"text": "Shop Now", "sub_text": "Limited Availability", "href": "/product/prod-5"},
          "image": {"src": "/producto5.png", "alt": "Polished Landscape Jasper"}
        }
      }
    ],
    "product_grid": {
      "title": "Latest Treasures",
      "items": [
        {
          "id": 1,
          "name": "Obsidian Cube",
          "slug": "obsidian-cube",
          "price": 120.00,
          "currency": "USD",
          "image": "/products/obsidian.png",
          "category": "Sculpture",
          "is_new": true,
          "is_featured": false
        }
      ]
    }
  }
}
```

## Docker

```bash
docker-compose up -d
```
