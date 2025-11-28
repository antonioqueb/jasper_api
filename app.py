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
        "service": "Jasper Home API",
        "version": "2.0.0"
    })


@app.route("/api/v1/home", methods=["GET"])
def get_home():
    """
    Obtener la configuración completa del Home.
    Retorna SEO + las 3 secciones fijas (Hero, Feature, Brand).
    """
    try:
        data = CMSService.get_home_content()
        return jsonify({"data": data})
    except Exception as e:
        # Log error for debugging
        print(f"Error fetching home: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )