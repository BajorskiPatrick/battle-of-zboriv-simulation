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
current_scenario_id = None  # ID aktualnie uruchomionego scenariusza

MAP_PATH = "assets/map/map.tmx"
RESULTS_FILE = "battle_results.json"

@app.route('/')
def index():
    """Główna strona z interfejsem konfiguracji"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Strona dashboardu analitycznego wyników bitew"""
    return render_template('dashboard.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serwuje pliki statyczne (sprite'y, mapy) z folderu assets"""
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
    return send_from_directory(assets_dir, filename)

@app.route('/api/battle-results', methods=['GET'])
def get_battle_results():
    """Zwraca zapisane wyniki bitew z battle_results.json"""
    try:
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = []
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/unit-types', methods=['GET'])
def get_unit_types():
    """Zwraca dostępne typy jednostek z parametrami"""
    # Inicjalizujemy model tylko po to, by pobrać parametry
    model = BattleOfZborowModel(MAP_PATH, {})
    
    # Lista jednostek kozackich do poprawnego przypisania frakcji
    cossack_units_list = ["Jazda Tatarska", "Piechota Kozacka", "Czern", "Jazda Kozacka", "Artyleria Kozacka"]
    
    unit_types = {}
    for unit_name, params in model.unit_params.items():
        # Określ frakcję na podstawie listy lub nazwy
        if unit_name in cossack_units_list or "Kozacka" in unit_name or "Tatarska" in unit_name:
            faction = "Kozacy/Tatarzy"
        else:
            faction = "Armia Koronna"
            
        unit_types[unit_name] = {
            "faction": faction,
            "hp": params["hp"],
            "morale": params["morale"],
            "discipline": params.get("discipline", 50), # Dodajemy nowe pole do API
            "range": params["range"],
            "damage": params.get("melee_damage", 0), # Wyświetlamy melee jako główne
            "speed": params["speed"],
            "description": params["description"],
            "sprite_path": params["sprite_path"]
        }
    
    return jsonify(unit_types)

@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    """Zwraca predefiniowane scenariusze bitwy z nowymi jednostkami"""
    
    # Lista wszystkich możliwych jednostek
    all_units = [
        "Husaria", "Pancerni", "Rajtaria", "Dragonia", "Piechota Niemiecka", 
        "Pospolite Ruszenie", "Czeladz Obozowa", "Artyleria Koronna",
        "Jazda Tatarska", "Piechota Kozacka", "Czern", "Jazda Kozacka", "Artyleria Kozacka"
    ]

    scenarios = {
        "scenario_1": {
            "id": "scenario_1",
            "name": "Dzień 1: Chaos na Przeprawie (15 VIII)",
            "description": "Atak na przeprawę. Wojska koronne (niebieskie) utknęły na mostach i lewym brzegu. Tatarzy atakują z lasów po lewej.",
            "units": {
                # --- Armia Koronna (Utknięta na przeprawie) ---
                "Pospolite Ruszenie": 10, # Panika na brzegu
                "Czeladz Obozowa": 6,     # Tabory blokujące mosty
                "Pancerni": 4,            # Osłona
                "Husaria": 2,             # Próba kontrataku
                
                # --- Atakujący (Tatarzy z lewej strony mapy) ---
                "Jazda Tatarska": 16,     # Szybki atak z lasu
                "Jazda Kozacka": 4,       # Wsparcie

                "_deployment": {
                    # Polacy stłoczeni przy rzece i mostach (X: 30-60)
                    "Czeladz Obozowa": {"x": [35, 55], "y": [30, 70]}, # Na mostach
                    "Pospolite Ruszenie": {"x": [25, 45], "y": [20, 80]}, # Przed mostami (lewy brzeg)
                    "Pancerni": {"x": [45, 60], "y": [10, 90]},           # Już przeprawieni (prawy brzeg)
                    "Husaria": {"x": [50, 65], "y": [40, 60]},            
                    
                    # Tatarzy wyłaniają się z lewej krawędzi mapy
                    "Jazda Tatarska": {"x": [2, 20], "y": [10, 90]},
                    "Jazda Kozacka": {"x": [2, 15], "y": [40, 60]}
                }
            }
        },
        "scenario_2": {
            "id": "scenario_2",
            "name": "Dzień 2: Obrona Wałów (16 VIII)",
            "description": "Główna faza bitwy. Polacy obsadzają fortyfikacje po prawej stronie mapy. Kozacy szturmują przez przedpole.",
            "units": {
                # --- Obrońcy (Za murami/wałami po prawej) ---
                "Piechota Niemiecka": 10, # Na wałach
                "Dragonia": 6,            # Mobilna obrona luk
                "Artyleria Koronna": 3,   # W bastionach
                "Husaria": 3,             # Odwód wewnątrz miasta
                
                # --- Atakujący (Szturm ze środka mapy) ---
                "Piechota Kozacka": 18,   # Główna siła
                "Czern": 12,              # Mięso armatnie
                "Artyleria Kozacka": 3,   # Ostrzał wałów
                "Jazda Tatarska": 5,      # Czeka na tyłach

                "_deployment": {
                    # Polacy w fortyfikacjach (Prawa strona, X > 110)
                    "Piechota Niemiecka": {"x": [110, 125], "y": [15, 85]}, # Pierwsza linia wałów
                    "Artyleria Koronna": {"x": [115, 130], "y": [20, 80]},  # Bastiony
                    "Dragonia": {"x": [120, 140], "y": [10, 90]},           # Wewnątrz
                    "Husaria": {"x": [130, 150], "y": [40, 60]},            # Centrum miasta
                    
                    # Kozacy na otwartym polu (Środek mapy, X: 50-90)
                    "Piechota Kozacka": {"x": [60, 95], "y": [10, 90]},
                    "Czern": {"x": [50, 80], "y": [20, 80]},
                    "Artyleria Kozacka": {"x": [40, 60], "y": [30, 70]},
                    "Jazda Tatarska": {"x": [30, 50], "y": [10, 90]} # Za rzeką/na mostach
                }
            }
        },
        "scenario_3": {
            "id": "scenario_3",
            "name": "Kryzys: Kontratak Czeladzi",
            "description": "Krytyczny moment. Wróg wdarł się do miasta (prawa strona). Czeladź broni centrum obozu.",
            "units": {
                # --- Obrońcy (Wciśnięci głęboko w miasto) ---
                "Czeladz Obozowa": 20,   
                "Dragonia": 4,           
                "Pospolite Ruszenie": 2, 
                
                # --- Atakujący (Już wewnątrz fortyfikacji) ---
                "Piechota Kozacka": 12,   
                "Jazda Kozacka": 4,

                "_deployment": {
                    # Polacy w samym centrum miasta (X: 130-155)
                    "Czeladz Obozowa": {"x": [135, 155], "y": [30, 70]}, 
                    "Dragonia": {"x": [130, 145], "y": [20, 80]},
                    
                    # Wróg przełamał wały (X: 110-125)
                    "Piechota Kozacka": {"x": [110, 130], "y": [15, 85]},
                    "Jazda Kozacka": {"x": [100, 120], "y": [40, 60]}
                }
            }
        },
        "scenario_4": {
            "id": "scenario_4",
            "name": "Hipotetyczne: Bitwa na Przedpolu",
            "description": "Jan Kazimierz wyprowadza wojska przed wały (na środek mapy), by wydać bitwę w polu.",
            "units": {
                "Piechota Niemiecka": 8,
                "Husaria": 6,            
                "Pancerni": 8,
                "Dragonia": 4,
                "Piechota Kozacka": 12,
                "Jazda Tatarska": 12,
                "Jazda Kozacka": 8,
                "_deployment": {
                    # Polacy na środku mapy (przed wałami)
                    "Piechota Niemiecka": {"x": [90, 105], "y": [20, 80]}, 
                    "Husaria": {"x": [100, 110], "y": [30, 70]},            
                    "Pancerni": {"x": [90, 105], "y": [10, 90]},            
                    
                    # Wróg atakuje od rzeki
                    "Piechota Kozacka": {"x": [50, 70], "y": [20, 80]},
                    "Jazda Kozacka": {"x": [40, 60], "y": [10, 90]},
                    "Jazda Tatarska": {"x": [30, 50], "y": [5, 95]}
                }
            }
        },
        "scenario_5": {
            "id": "scenario_5",
            "name": "Potyczka nad Rzeką (Zwiad)",
            "description": "Walka podjazdowa o kontrolę nad mostami na rzece Strypie.",
            "units": {
                "Pancerni": 5,
                "Dragonia": 2,
                "Jazda Tatarska": 5,
                "Jazda Kozacka": 3,
                "_deployment": {
                    # Polacy bronią mostów (Prawy brzeg)
                    "Pancerni": {"x": [50, 60], "y": [30, 70]},
                    "Dragonia": {"x": [55, 65], "y": [40, 60]},
                    
                    # Tatarzy próbują sforsować rzekę (Lewy brzeg)
                    "Jazda Tatarska": {"x": [20, 35], "y": [20, 80]},
                    "Jazda Kozacka": {"x": [25, 40], "y": [40, 60]}
                }
            }
        },
        "scenario_6": {
            "id": "scenario_6",
            "name": "Szarża Husarii z Obozu",
            "description": "Wycieczka Husarii zza wałów przeciwko oblegającym wojskom.",
            "units": {
                "Husaria": 10,
                "Pancerni": 4,
                "Piechota Kozacka": 10,
                "Czern": 15,
                "Jazda Tatarska": 5,
                "_deployment": {
                    # Polacy startują z miasta/bram (Prawa strona)
                    "Husaria": {"x": [110, 125], "y": [10, 90]}, # Rozpędzona linia
                    "Pancerni": {"x": [120, 130], "y": [20, 80]},
                    
                    # Wróg na przedpolu (Środek)
                    "Czern": {"x": [70, 90], "y": [10, 90]},
                    "Piechota Kozacka": {"x": [60, 80], "y": [20, 80]}, 
                    "Jazda Tatarska": {"x": [40, 60], "y": [5, 95]}
                }
            }
        },
        "scenario_7": {
            "id": "scenario_7",
            "name": "Rzeczywisty: Pełne Oblężenie",
            "description": "Historyczna dysproporcja sił (1:4). Polacy zamknięci w fortyfikacjach (prawo), wróg zalewa całą mapę.",
            "units": {
                "Piechota Niemiecka": 6,
                "Dragonia": 4,
                "Husaria": 2,
                "Pospolite Ruszenie": 6,
                "Artyleria Koronna": 2,
                
                # Ogromna przewaga wroga
                "Piechota Kozacka": 25,
                "Czern": 20,
                "Jazda Tatarska": 15,
                "Artyleria Kozacka": 4,
                "_deployment": {
                    # Polacy: tylko wewnątrz murów (Prawa krawędź)
                    "Piechota Niemiecka": {"x": [115, 130], "y": [15, 85]},
                    "Artyleria Koronna": {"x": [120, 135], "y": [25, 75]},
                    "Dragonia": {"x": [125, 145], "y": [10, 90]},
                    "Husaria": {"x": [140, 155], "y": [40, 60]},
                    "Pospolite Ruszenie": {"x": [135, 155], "y": [10, 90]},
                    
                    # Wróg: Od rzeki aż pod mury
                    "Piechota Kozacka": {"x": [50, 100], "y": [5, 95]}, # Podchodzą pod mury
                    "Czern": {"x": [40, 80], "y": [10, 90]},
                    "Jazda Tatarska": {"x": [5, 60], "y": [0, 100]},   # Panują na polu
                    "Artyleria Kozacka": {"x": [30, 50], "y": [20, 80]}
                }
            }
        }
    }
    
    # Uzupełnij zerami brakujące jednostki (dla bezpieczeństwa frontendu)
    for scenario in scenarios.values():
        for unit in all_units:
            if unit not in scenario["units"]:
                scenario["units"][unit] = 0
                
    return jsonify(scenarios)

@app.route('/api/map-data', methods=['GET'])
def get_map_data():
    """Zwraca dane mapy z Tiled (layout tiles)"""
    import pytmx
    import xml.etree.ElementTree as ET
    
    try:
        tmx_data = pytmx.TiledMap(MAP_PATH)
        
        # Załaduj XML bezpośrednio, aby dostać surowe GID
        tree = ET.parse(MAP_PATH)
        root = tree.getroot()
        
        # Znajdź warstwę "Teren"
        terrain_layer_element = None
        for layer in root.findall('layer'):
            if layer.get('name') == 'Teren':
                terrain_layer_element = layer
                break
        
        if terrain_layer_element is None:
            return jsonify({"error": "Layer 'Teren' not found"}), 404
        
        # Pobierz surowe dane CSV z warstwy
        data_element = terrain_layer_element.find('data')
        if data_element is None or data_element.get('encoding') != 'csv':
            return jsonify({"error": "Invalid layer data format"}), 500
        
        csv_data = data_element.text.strip()
        
        # Parsuj CSV na listę liczb
        raw_gids = [int(x.strip()) for x in csv_data.split(',') if x.strip()]
        
        # Konwertuj na tablicę 2D - zachowaj flagi transformacji jako osobny obiekt
        tile_grid = []
        flip_flags = []  # Osobna tablica dla flag transformacji
        width = int(terrain_layer_element.get('width'))
        height = int(terrain_layer_element.get('height'))
        
        FLIPPED_HORIZONTALLY = 0x80000000
        FLIPPED_VERTICALLY = 0x40000000
        FLIPPED_DIAGONALLY = 0x20000000
        
        for y in range(height):
            row = []
            flags_row = []
            for x in range(width):
                idx = y * width + x
                if idx < len(raw_gids):
                    raw_gid = raw_gids[idx]
                    
                    # Wyodrębnij flagi transformacji
                    flip_h = bool(raw_gid & FLIPPED_HORIZONTALLY)
                    flip_v = bool(raw_gid & FLIPPED_VERTICALLY)
                    flip_d = bool(raw_gid & FLIPPED_DIAGONALLY)
                    
                    # Czyste GID bez flag
                    gid = raw_gid & 0x1FFFFFFF
                    
                    flags_row.append({
                        'h': flip_h,
                        'v': flip_v,
                        'd': flip_d
                    })
                else:
                    gid = 0
                    flags_row.append({'h': False, 'v': False, 'd': False})
                    
                row.append(gid)
            tile_grid.append(row)
            flip_flags.append(flags_row)
        
        # Pobierz informacje o tilesetcie
        tileset = tmx_data.tilesets[0] if len(tmx_data.tilesets) > 0 else None
        
        # Domyślne wartości
        tileset_image_path = "assets/map/tileset_legacy.png"
        tileset_columns = 32
        tileset_spacing = 1
        tileset_firstgid = 1
        
        if tileset:
            # Bezpieczne pobieranie ścieżki
            try:
                if hasattr(tileset, 'image') and tileset.image:
                    if isinstance(tileset.image, str):
                        tileset_image_path = f"assets/map/{os.path.basename(tileset.image)}"
                    elif hasattr(tileset.image, 'source'):
                        tileset_image_path = f"assets/map/{os.path.basename(tileset.image.source)}"
            except Exception as img_err:
                print(f"Warning: Error extracting tileset image path: {img_err}")

            # Jeśli to nowa mapa, wymuś poprawny tileset (ponieważ .tsx może mieszać ścieżki)
            if "map" in MAP_PATH:
                tileset_image_path = "assets/map/tileset_legacy.png"

            tileset_columns = tileset.columns if hasattr(tileset, 'columns') else 32
            tileset_spacing = tileset.spacing if hasattr(tileset, 'spacing') else 0
            tileset_firstgid = tileset.firstgid if hasattr(tileset, 'firstgid') else 1
        
        map_info = {
            "width": tmx_data.width,
            "height": tmx_data.height,
            "tile_width": tmx_data.tilewidth,
            "tile_height": tmx_data.tileheight,
            "tiles": tile_grid,
            "flip_flags": flip_flags,  # Dodaj flagi transformacji
            "tileset_image": tileset_image_path,
            "tileset_columns": tileset_columns,
            "tileset_spacing": tileset_spacing,
            "tileset_firstgid": tileset_firstgid
        }
        
        print(f"DEBUG: Map loaded successfully. Size: {tmx_data.width}x{tmx_data.height}. Tileset: {tileset_image_path}")
        return jsonify(map_info)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRITICAL ERROR loading map data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/start-simulation', methods=['POST'])
def start_simulation():
    """Rozpoczyna nową symulację z uwzględnieniem pogody."""
    global simulation, simulation_running, current_scenario_id
    
    data = request.json
    scenario_id = data.get('scenario_id', None)
    weather = data.get('weather', 'clear')  # Odbieramy pogodę, domyślnie czysto
    
    all_scenarios_response = get_scenarios() 
    all_scenarios = all_scenarios_response.json
    
    final_config = {}
    
    if scenario_id == 'custom':
        final_config = data.get('units_config', {})
    else:
        if scenario_id in all_scenarios:
            final_config = all_scenarios[scenario_id]['units']
        else:
            final_config = data.get('units_config', {})

    print(f"Start scenariusza: {scenario_id}, Pogoda: {weather}")
    
    with simulation_lock:
        # Przekazujemy pogodę do konstruktora
        simulation = BattleOfZborowModel(MAP_PATH, final_config, weather=weather)
        simulation_running = True
        current_scenario_id = scenario_id
    
    return jsonify({"status": "started", "message": "Symulacja rozpoczęta"})

@app.route('/api/stop-simulation', methods=['POST'])
def stop_simulation():
    """Zatrzymuje i czyści symulację"""
    global simulation, simulation_running, current_scenario_id
    
    with simulation_lock:
        simulation_running = False
        simulation = None  # Wyczyść symulację
        current_scenario_id = None
    
    return jsonify({"status": "stopped", "message": "Symulacja zatrzymana i wyczyszczona"})

@app.route('/api/save-battle-result', methods=['POST'])
def save_battle_result():
    """Zapisuje wynik bitwy do pliku JSON"""
    global current_scenario_id
    
    try:
        data = request.json
        
        # Przygotuj wynik bitwy
        battle_result = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "scenario_id": current_scenario_id or data.get('scenario_id', 'unknown'),
            "scenario_name": data.get('scenario_name', 'Unknown'),
            "winner": data.get('winner', 'Unknown'),
            "survivors": data.get('survivors', 0),
            "crown_count": data.get('crown_count', 0),
            "cossack_count": data.get('cossack_count', 0),
            "total_agents": data.get('total_agents', 0),
            "initial_units": data.get('initial_units', {})
        }
        
        # Wczytaj istniejące wyniki lub stwórz nową listę
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                results = json.load(f)
        else:
            results = []
        
        # Dodaj nowy wynik
        results.append(battle_result)
        
        # Zapisz z powrotem do pliku
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"Zapisano wynik bitwy: {battle_result}")
        
        return jsonify({"status": "saved", "message": "Wynik bitwy zapisany"})
    
    except Exception as e:
        print(f"Błąd zapisywania wyniku bitwy: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/simulation-step', methods=['GET'])
def simulation_step():
    """Wykonuje jeden krok symulacji i zwraca aktualny stan"""
    global simulation, simulation_running
    
    with simulation_lock:
        # Sprawdź symulację wewnątrz locka
        if simulation is None:
            return jsonify({"error": "Symulacja nie została rozpoczęta"}), 400
        
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
        
        # Przygotuj strefy leczenia
        healing_zones_data = [{"x": x, "y": y} for x, y in simulation.healing_zones]

        return jsonify({
            "agents": agents_data,
            "stats": stats,
            "battle_status": battle_status,
            "running": simulation_running,
            "map_width": simulation.grid.width,
            "map_height": simulation.grid.height,
            "healing_zones": healing_zones_data
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
