from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import json
import io
import base64
from PIL import Image
import numpy as np
from simulation.model import BattleOfZborowModel
from simulation.web_renderer import WebRenderer
import threading
import time
import os

app = Flask(__name__)
CORS(app)

# Globalna instancja symulacji
simulation = None
simulation_lock = threading.Lock()
simulation_running = False

MAP_PATH = "assets/map/zborow_battlefield.tmx"

@app.route('/')
def index():
    """Główna strona z interfejsem konfiguracji"""
    return render_template('index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serwuje pliki statyczne (sprite'y, mapy) z folderu assets"""
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
    return send_from_directory(assets_dir, filename)

@app.route('/api/unit-types', methods=['GET'])
def get_unit_types():
    """Zwraca dostępne typy jednostek z parametrami"""
    model = BattleOfZborowModel(MAP_PATH, {})
    
    unit_types = {}
    for unit_name, params in model.unit_params.items():
        # Określ frakcję na podstawie nazwy jednostki
        if "Kozacka" in unit_name or "Tatarska" in unit_name:
            faction = "Kozacy/Tatarzy"
        else:
            faction = "Armia Koronna"
        print(unit_name, faction)
        unit_types[unit_name] = {
            "faction": faction,
            "hp": params["hp"],
            "morale": params["morale"],
            "range": params["range"],
            "damage": params["damage"],
            "speed": params["speed"],
            "description": params["description"],
            "sprite_path": params["sprite_path"]
        }
    
    return jsonify(unit_types)

@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    """Zwraca predefiniowane scenariusze bitwy"""
    units = ["Piechota", "Jazda", "Piechota Kozacka", "Jazda Tatarska", "Dragonia", "Pospolite Ruszenie"]
    scenarios = {
        "scenario_1": {
            "id": "scenario_1",
            "name": "Scenariusz Podstawowy",
            "description": "Zbalansowana bitwa z równą liczbą jednostek",
            "units": {
                "Piechota": 5,
                "Jazda": 3,
                "Piechota Kozacka": 5,
                "Jazda Tatarska": 5
            }
        },
        "scenario_2": {
            "id": "scenario_2",
            "name": "Przewaga Jazdy",
            "description": "Kozacy wykorzystują mobilność jazdy tatarskiej",
            "units": {
                "Piechota": 3,
                "Jazda": 2,
                "Piechota Kozacka": 3,
                "Jazda Tatarska": 8
            }
        },
        "scenario_3": {
            "id": "scenario_3",
            "name": "Szturm Piechoty",
            "description": "Obfite siły piechoty po obu stronach",
            "units": {
                "Piechota": 8,
                "Dragonia": 4,
                "Piechota Kozacka": 10,
                "Jazda Tatarska": 2
            }
        },
        "scenario_4": {
            "id": "scenario_4",
            "name": "Armia Koronna Dominuje",
            "description": "Przewaga liczebna po stronie Koronnej",
            "units": {
                "Piechota": 10,
                "Jazda": 6,
                "Dragonia": 4,
                "Piechota Kozacka": 4,
                "Jazda Tatarska": 3
            }
        },
        "scenario_5": {
            "id": "scenario_5",
            "name": "Mała Potyczka",
            "description": "Szybka bitwa z mniejszą liczbą jednostek",
            "units": {
                "Piechota": 3,
                "Jazda": 2,
                "Piechota Kozacka": 3,
                "Jazda Tatarska": 2
            }
        },
        "scenario_6": {
            "id": "scenario_6",
            "name": "Wielka Bitwa",
            "description": "Masywne starcie z dużą liczbą jednostek",
            "units": {
                "Piechota": 12,
                "Jazda": 8,
                "Dragonia": 6,
                "Pospolite Ruszenie": 4,
                "Piechota Kozacka": 12,
                "Jazda Tatarska": 10
            }
        },
        "scenario_7": {
            "id": "scenario_7",
            "name": "Scenariusz Rzeczywisty (1649)",
            "description": "Oparte na historycznych danych z Bitwy pod Zborowem (W. Kucharski) - Armia Koronna ~15 000, Kozacy ~40 000, Tatarzy 50-60 000. Dokładny stosunek 1:6.3",
            "units": {
                "Piechota": 3,
                "Jazda": 4,
                "Dragonia": 2,
                "Pospolite Ruszenie": 3,
                "Piechota Kozacka": 32,
                "Jazda Tatarska": 44
            }
        }
    }
    for scenario in scenarios:
        for unit in units:
            if unit not in scenarios[scenario]["units"]:
                scenarios[scenario]["units"][unit] = 0
    return jsonify(scenarios)

@app.route('/api/map-data', methods=['GET'])
def get_map_data():
    """Zwraca dane mapy z Tiled (layout tiles)"""
    import pytmx
    
    try:
        tmx_data = pytmx.TiledMap(MAP_PATH)
        
        # Pobierz warstwę terenu
        terrain_layer = tmx_data.get_layer_by_name("Teren")
        
        # Utwórz tablicę 2D z ID tiles
        tile_grid = []
        for y in range(tmx_data.height):
            row = []
            for x in range(tmx_data.width):
                gid = terrain_layer.data[y][x]
                row.append(gid)
            tile_grid.append(row)
        
        map_info = {
            "width": tmx_data.width,
            "height": tmx_data.height,
            "tile_width": tmx_data.tilewidth,
            "tile_height": tmx_data.tileheight,
            "tiles": tile_grid,
            "tileset_image": "assets/map/tileset.png"
        }
        
        return jsonify(map_info)
    except Exception as e:
        print(f"Error loading map data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/start-simulation', methods=['POST'])
def start_simulation():
    """Rozpoczyna nową symulację z podaną konfiguracją jednostek"""
    global simulation, simulation_running
    
    config = request.json
    print(f"Otrzymana konfiguracja: {config}")
    
    with simulation_lock:
        # Stwórz nowy model z konfiguracją
        simulation = BattleOfZborowModel(MAP_PATH, config)
        simulation_running = True
    
    return jsonify({"status": "started", "message": "Symulacja rozpoczęta"})

@app.route('/api/stop-simulation', methods=['POST'])
def stop_simulation():
    """Zatrzymuje i czyści symulację"""
    global simulation, simulation_running
    
    with simulation_lock:
        simulation_running = False
        simulation = None  # Wyczyść symulację
    
    return jsonify({"status": "stopped", "message": "Symulacja zatrzymana i wyczyszczona"})

@app.route('/api/simulation-step', methods=['GET'])
def simulation_step():
    """Wykonuje jeden krok symulacji i zwraca aktualny stan"""
    global simulation, simulation_running
    
    if simulation is None:
        return jsonify({"error": "Symulacja nie została rozpoczęta"}), 400
    
    with simulation_lock:
        if simulation_running:
            print(f"Executing step... Agents: {len(simulation.schedule.agents)}")
            simulation.step()
        
        # Zbierz informacje o aktualnym stanie (TYLKO ŻYWI AGENCI)
        agents_data = []
        for agent in simulation.schedule.agents:
            # Pomiń agentów z hp <= 0 (nie powinni już być renderowani)
            if agent.hp <= 0:
                continue
                
            pos = agent.get_pos_tuple()
            agents_data.append({
                "id": agent.unique_id,
                "faction": agent.faction,
                "unit_type": agent.unit_type,
                "x": pos[0],
                "y": pos[1],
                "hp": agent.hp,
                "max_hp": agent.max_hp,
                "morale": agent.morale,
                "max_morale": agent.max_morale,
                "state": agent.state,
                "sprite_path": simulation.unit_params[agent.unit_type]["sprite_path"]
            })
        
        stats = {
            "crown_count": len([a for a in simulation.schedule.agents if a.faction == "Armia Koronna" and a.hp > 0]),
            "cossack_count": len([a for a in simulation.schedule.agents if a.faction == "Kozacy/Tatarzy" and a.hp > 0]),
            "total_agents": len([a for a in simulation.schedule.agents if a.hp > 0])
        }
        
        # Sprawdź status bitwy
        battle_status = simulation.get_battle_status()
        
        return jsonify({
            "agents": agents_data,
            "stats": stats,
            "battle_status": battle_status,
            "running": simulation_running,
            "map_width": simulation.width,
            "map_height": simulation.height
        })

@app.route('/api/simulation-frame', methods=['GET'])
def get_simulation_frame():
    """Generuje i zwraca obraz aktualnego stanu symulacji"""
    global simulation
    
    if simulation is None:
        return jsonify({"error": "Symulacja nie została rozpoczęta"}), 400
    
    with simulation_lock:
        renderer = WebRenderer(simulation)
        frame = renderer.render_frame()
        
        # Konwertuj do base64
        buffered = io.BytesIO()
        frame.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({
            "frame": f"data:image/png;base64,{img_str}",
            "running": simulation_running
        })

def stream_simulation():
    """Generator do streamowania klatek symulacji"""
    global simulation, simulation_running
    
    while simulation_running:
        if simulation is not None:
            with simulation_lock:
                simulation.step()
                renderer = WebRenderer(simulation)
                frame = renderer.render_frame()
                
                buffered = io.BytesIO()
                frame.save(buffered, format="JPEG", quality=85)
                img_bytes = buffered.getvalue()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + img_bytes + b'\r\n')
            
            time.sleep(0.2)  # 5 FPS
        else:
            time.sleep(0.1)

@app.route('/api/video-feed')
def video_feed():
    """Endpoint do streamowania wideo (MJPEG)"""
    return Response(stream_simulation(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
