from flask import Flask, render_template, jsonify, request
from datetime import datetime
import json
import os
from typing import List, Dict

from value_finder import ValueEngine
from config.settings import settings

app = Flask(__name__, 
            template_folder='../../templates',
            static_folder='../../static')

# Instancia global del engine
engine = None


def get_latest_results() -> Dict:
    """Obtiene los últimos resultados guardados."""
    results_dir = "results"
    
    if not os.path.exists(results_dir):
        return {"picks": [], "total_picks": 0, "timestamp": None}
    
    files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
    
    if not files:
        return {"picks": [], "total_picks": 0, "timestamp": None}
    
    # Obtener el archivo más reciente
    latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(results_dir, f)))
    
    with open(os.path.join(results_dir, latest_file), 'r', encoding='utf-8') as f:
        return json.load(f)


@app.route('/')
def index():
    """Página principal."""
    return render_template('index.html', settings=settings)


@app.route('/results')
def results():
    """Página de resultados."""
    data = get_latest_results()
    return render_template('results.html', data=data)


@app.route('/api/scan', methods=['POST'])
def api_scan():
    """Endpoint para iniciar un nuevo escaneo."""
    global engine
    
    try:
        if engine is None:
            engine = ValueEngine()
        
        # Ejecutar en background (en producción usar Celery o similar)
        engine.run_pipeline()
        
        return jsonify({
            "status": "success",
            "message": "Escaneo completado",
            "picks_found": len(engine.value_picks)
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/results/latest')
def api_latest_results():
    """API endpoint para obtener últimos resultados."""
    data = get_latest_results()
    return jsonify(data)


@app.route('/api/leagues')
def api_leagues():
    """API endpoint para obtener ligas configuradas."""
    config_path = "config/leagues.json"
    
    if not os.path.exists(config_path):
        return jsonify([])
    
    with open(config_path, 'r', encoding='utf-8') as f:
        leagues = json.load(f)
    
    return jsonify(leagues)


@app.route('/api/stats')
def api_stats():
    """API endpoint para estadísticas generales."""
    data = get_latest_results()
    
    if not data["picks"]:
        return jsonify({
            "total_picks": 0,
            "avg_ev": 0,
            "avg_stake": 0,
            "leagues_analyzed": 0
        })
    
    picks = data["picks"]
    
    stats = {
        "total_picks": len(picks),
        "avg_ev": round(sum(p["expected_value"] for p in picks) / len(picks), 2),
        "avg_stake": round(sum(p["kelly_stake"] for p in picks) / len(picks), 2),
        "leagues_analyzed": len(set(p["league"] for p in picks)),
        "last_update": data.get("timestamp")
    }
    
    return jsonify(stats)


def run_web_app():
    """Inicia el servidor web."""
    app.run(
        host=settings.FLASK_HOST,
        port=settings.FLASK_PORT,
        debug=settings.FLASK_DEBUG
    )


if __name__ == '__main__':
    run_web_app()
