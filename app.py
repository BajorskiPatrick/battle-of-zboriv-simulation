from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    Response,
    send_from_directory,
)
from flask_cors import CORS
import json
import io
import base64
from simulation.model import BattleOfZborowModel
from simulation.web_renderer import WebRenderer
import threading
import time
import os
import uuid

app = Flask(__name__)
CORS(app)

simulation = None
simulation_lock = threading.Lock()
simulation_running = False
current_scenario_id = None

MAP_PATH = "assets/map/map.tmx"
RESULTS_FILE = "battle_results.json"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/heatmap/<result_id>")
def heatmap_view(result_id):
    return render_template("heatmap.html", result_id=result_id)


@app.route("/assets/<path:filename>")
def serve_assets(filename):
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    return send_from_directory(assets_dir, filename)


@app.route("/api/battle-results", methods=["GET"])
def get_battle_results():
    try:
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/battle-result/<result_id>", methods=["GET"])
def get_single_battle_result(result_id):
    try:
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            result = next((item for item in data if item.get("id") == result_id), None)

            if result:
                return jsonify({"ok": True, "data": result})
            else:
                return jsonify({"ok": False, "error": "Result not found"}), 404
        else:
            return jsonify({"ok": False, "error": "No results file"}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/unit-types", methods=["GET"])
def get_unit_types():
    model = BattleOfZborowModel(MAP_PATH, {})

    cossack_units_list = [
        "Jazda Tatarska",
        "Piechota Kozacka",
        "Czern",
        "Jazda Kozacka",
        "Artyleria Kozacka",
    ]

    unit_types = {}
    for unit_name, params in model.unit_params.items():
        if (
            unit_name in cossack_units_list
            or "Kozacka" in unit_name
            or "Tatarska" in unit_name
        ):
            faction = "Kozacy/Tatarzy"
        else:
            faction = "Armia Koronna"

        unit_types[unit_name] = {
            "faction": faction,
            "hp": params["hp"],
            "morale": params["morale"],
            "discipline": params.get("discipline", 50),
            "range": params["range"],
            "damage": params.get("melee_damage", 0),
            "speed": params["speed"],
            "description": params["description"],
            "sprite_path": params["sprite_path"],
        }

    return jsonify(unit_types)


@app.route("/api/scenarios", methods=["GET"])
def get_scenarios():

    all_units = [
        "Husaria",
        "Pancerni",
        "Rajtaria",
        "Dragonia",
        "Piechota Niemiecka",
        "Pospolite Ruszenie",
        "Czeladz Obozowa",
        "Artyleria Koronna",
        "Jazda Tatarska",
        "Piechota Kozacka",
        "Czern",
        "Jazda Kozacka",
        "Artyleria Kozacka",
    ]

    scenarios = {
        "scenario_1": {
            "id": "scenario_1",
            "name": "Dzień 1: Chaos na Przeprawie (15 VIII)",
            "description": "Atak na przeprawę. Wojska koronne (niebieskie) utknęły na mostach i lewym brzegu. Tatarzy atakują z lasów po lewej.",
            "units": {
                "Pospolite Ruszenie": 10,
                "Czeladz Obozowa": 6,
                "Pancerni": 4,
                "Husaria": 2,
                "Jazda Tatarska": 16,
                "Jazda Kozacka": 4,
                "_deployment": {
                    "Czeladz Obozowa": {"x": [35, 55], "y": [30, 70]},
                    "Pospolite Ruszenie": {
                        "x": [25, 45],
                        "y": [20, 80],
                    },
                    "Pancerni": {
                        "x": [45, 60],
                        "y": [10, 90],
                    },
                    "Husaria": {"x": [50, 65], "y": [40, 60]},
                    "Jazda Tatarska": {"x": [2, 20], "y": [10, 90]},
                    "Jazda Kozacka": {"x": [2, 15], "y": [40, 60]},
                },
            },
        },
        "scenario_2": {
            "id": "scenario_2",
            "name": "Dzień 2: Obrona Wałów (16 VIII)",
            "description": "Główna faza bitwy. Polacy obsadzają fortyfikacje po prawej stronie mapy. Kozacy szturmują przez przedpole.",
            "units": {
                "Piechota Niemiecka": 10,
                "Dragonia": 6,
                "Artyleria Koronna": 3,
                "Husaria": 3,
                "Piechota Kozacka": 18,
                "Czern": 12,
                "Artyleria Kozacka": 3,
                "Jazda Tatarska": 5,
                "_deployment": {
                    "Piechota Niemiecka": {
                        "x": [110, 125],
                        "y": [15, 85],
                    },
                    "Artyleria Koronna": {"x": [115, 130], "y": [20, 80]},
                    "Dragonia": {"x": [120, 140], "y": [10, 90]},
                    "Husaria": {"x": [130, 150], "y": [40, 60]},
                    "Piechota Kozacka": {"x": [60, 95], "y": [10, 90]},
                    "Czern": {"x": [50, 80], "y": [20, 80]},
                    "Artyleria Kozacka": {"x": [40, 60], "y": [30, 70]},
                    "Jazda Tatarska": {
                        "x": [30, 50],
                        "y": [10, 90],
                    },
                },
            },
        },
        "scenario_3": {
            "id": "scenario_3",
            "name": "Kryzys: Kontratak Czeladzi",
            "description": "Krytyczny moment. Wróg wdarł się do miasta (prawa strona). Czeladź broni centrum obozu.",
            "units": {
                "Czeladz Obozowa": 20,
                "Dragonia": 4,
                "Pospolite Ruszenie": 2,
                "Piechota Kozacka": 12,
                "Jazda Kozacka": 4,
                "_deployment": {
                    "Czeladz Obozowa": {"x": [135, 155], "y": [30, 70]},
                    "Dragonia": {"x": [130, 145], "y": [20, 80]},
                    "Piechota Kozacka": {"x": [110, 130], "y": [15, 85]},
                    "Jazda Kozacka": {"x": [100, 120], "y": [40, 60]},
                },
            },
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
                    "Piechota Niemiecka": {"x": [90, 105], "y": [20, 80]},
                    "Husaria": {"x": [100, 110], "y": [30, 70]},
                    "Pancerni": {"x": [90, 105], "y": [10, 90]},
                    "Piechota Kozacka": {"x": [50, 70], "y": [20, 80]},
                    "Jazda Kozacka": {"x": [40, 60], "y": [10, 90]},
                    "Jazda Tatarska": {"x": [30, 50], "y": [5, 95]},
                },
            },
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
                    "Pancerni": {"x": [50, 60], "y": [30, 70]},
                    "Dragonia": {"x": [55, 65], "y": [40, 60]},
                    "Jazda Tatarska": {"x": [20, 35], "y": [20, 80]},
                    "Jazda Kozacka": {"x": [25, 40], "y": [40, 60]},
                },
            },
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
                    "Husaria": {"x": [110, 125], "y": [10, 90]},
                    "Pancerni": {"x": [120, 130], "y": [20, 80]},
                    "Czern": {"x": [70, 90], "y": [10, 90]},
                    "Piechota Kozacka": {"x": [60, 80], "y": [20, 80]},
                    "Jazda Tatarska": {"x": [40, 60], "y": [5, 95]},
                },
            },
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
                "Piechota Kozacka": 25,
                "Czern": 20,
                "Jazda Tatarska": 15,
                "Artyleria Kozacka": 4,
                "_deployment": {
                    "Piechota Niemiecka": {"x": [115, 130], "y": [15, 85]},
                    "Artyleria Koronna": {"x": [120, 135], "y": [25, 75]},
                    "Dragonia": {"x": [125, 145], "y": [10, 90]},
                    "Husaria": {"x": [140, 155], "y": [40, 60]},
                    "Pospolite Ruszenie": {"x": [135, 155], "y": [10, 90]},
                    "Piechota Kozacka": {
                        "x": [50, 100],
                        "y": [5, 95],
                    },
                    "Czern": {"x": [40, 80], "y": [10, 90]},
                    "Jazda Tatarska": {"x": [5, 60], "y": [0, 100]},
                    "Artyleria Kozacka": {"x": [30, 50], "y": [20, 80]},
                },
            },
        },
    }

    for scenario in scenarios.values():
        for unit in all_units:
            if unit not in scenario["units"]:
                scenario["units"][unit] = 0

    return jsonify(scenarios)


@app.route("/api/map-data", methods=["GET"])
def get_map_data():
    import pytmx
    import xml.etree.ElementTree as ET

    try:
        tmx_data = pytmx.TiledMap(MAP_PATH)

        tree = ET.parse(MAP_PATH)
        root = tree.getroot()

        terrain_layer_element = None
        for layer in root.findall("layer"):
            if layer.get("name") == "Teren":
                terrain_layer_element = layer
                break

        if terrain_layer_element is None:
            return jsonify({"error": "Layer 'Teren' not found"}), 404

        data_element = terrain_layer_element.find("data")
        if data_element is None or data_element.get("encoding") != "csv":
            return jsonify({"error": "Invalid layer data format"}), 500

        csv_data = data_element.text.strip()

        raw_gids = [int(x.strip()) for x in csv_data.split(",") if x.strip()]

        tile_grid = []
        flip_flags = []
        width = int(terrain_layer_element.get("width"))
        height = int(terrain_layer_element.get("height"))

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

                    flip_h = bool(raw_gid & FLIPPED_HORIZONTALLY)
                    flip_v = bool(raw_gid & FLIPPED_VERTICALLY)
                    flip_d = bool(raw_gid & FLIPPED_DIAGONALLY)

                    gid = raw_gid & 0x1FFFFFFF

                    flags_row.append({"h": flip_h, "v": flip_v, "d": flip_d})
                else:
                    gid = 0
                    flags_row.append({"h": False, "v": False, "d": False})

                row.append(gid)
            tile_grid.append(row)
            flip_flags.append(flags_row)

        tileset = tmx_data.tilesets[0] if len(tmx_data.tilesets) > 0 else None

        tileset_image_path = "assets/map/tileset_legacy.png"
        tileset_columns = 32
        tileset_spacing = 1
        tileset_firstgid = 1

        if tileset:
            try:
                if hasattr(tileset, "image") and tileset.image:
                    if isinstance(tileset.image, str):
                        tileset_image_path = (
                            f"assets/map/{os.path.basename(tileset.image)}"
                        )
                    elif hasattr(tileset.image, "source"):
                        tileset_image_path = (
                            f"assets/map/{os.path.basename(tileset.image.source)}"
                        )
            except Exception as img_err:
                print(f"Warning: Error extracting tileset image path: {img_err}")

            if "map" in MAP_PATH:
                tileset_image_path = "assets/map/tileset_legacy.png"

            tileset_columns = tileset.columns if hasattr(tileset, "columns") else 32
            tileset_spacing = tileset.spacing if hasattr(tileset, "spacing") else 0
            tileset_firstgid = tileset.firstgid if hasattr(tileset, "firstgid") else 1

        map_info = {
            "width": tmx_data.width,
            "height": tmx_data.height,
            "tile_width": tmx_data.tilewidth,
            "tile_height": tmx_data.tileheight,
            "tiles": tile_grid,
            "flip_flags": flip_flags,
            "tileset_image": tileset_image_path,
            "tileset_columns": tileset_columns,
            "tileset_spacing": tileset_spacing,
            "tileset_firstgid": tileset_firstgid,
        }

        print(
            f"DEBUG: Map loaded successfully. Size: {tmx_data.width}x{tmx_data.height}. Tileset: {tileset_image_path}"
        )
        return jsonify(map_info)

    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"CRITICAL ERROR loading map data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/start-simulation", methods=["POST"])
def start_simulation():
    global simulation, simulation_running, current_scenario_id

    data = request.json
    scenario_id = data.get("scenario_id", None)
    weather = data.get("weather", "clear")

    all_scenarios_response = get_scenarios()
    all_scenarios = all_scenarios_response.json

    final_config = {}

    if scenario_id == "custom":
        final_config = data.get("units_config", {})
    else:
        if scenario_id in all_scenarios:
            final_config = all_scenarios[scenario_id]["units"]
        else:
            final_config = data.get("units_config", {})

    print(f"Start scenariusza: {scenario_id}, Pogoda: {weather}")

    with simulation_lock:
        simulation = BattleOfZborowModel(MAP_PATH, final_config, weather=weather)
        simulation_running = True
        current_scenario_id = scenario_id

    return jsonify({"status": "started", "message": "Symulacja rozpoczęta"})


@app.route("/api/stop-simulation", methods=["POST"])
def stop_simulation():
    global simulation, simulation_running, current_scenario_id

    with simulation_lock:
        simulation_running = False
        simulation = None
        current_scenario_id = None

    return jsonify(
        {"status": "stopped", "message": "Symulacja zatrzymana i wyczyszczona"}
    )


@app.route("/api/save-battle-result", methods=["POST"])
def save_battle_result():
    global current_scenario_id, simulation

    try:
        data = request.json

        heatmap_data = None
        with simulation_lock:
            if simulation is not None:
                h_crown = getattr(simulation, "heatmap_crown", None)
                h_cossack = getattr(simulation, "heatmap_cossack", None)

                if h_crown is not None and h_cossack is not None:
                    heatmap_data = {
                        "crown": h_crown.tolist(),
                        "cossack": h_cossack.tolist(),
                        "width": simulation.width,
                        "height": simulation.height,
                    }

        battle_result = {
            "id": str(uuid.uuid4()),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "scenario_id": current_scenario_id or data.get("scenario_id", "unknown"),
            "scenario_name": data.get("scenario_name", "Unknown"),
            "winner": data.get("winner", "Unknown"),
            "survivors": data.get("survivors", 0),
            "crown_count": data.get("crown_count", 0),
            "cossack_count": data.get("cossack_count", 0),
            "total_agents": data.get("total_agents", 0),
            "initial_units": data.get("initial_units", {}),
            "heatmap": heatmap_data,
        }

        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
        else:
            results = []

        results.append(battle_result)

        with open(RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"Zapisano wynik bitwy: {battle_result}")

        return jsonify({"status": "saved", "message": "Wynik bitwy zapisany"})

    except Exception as e:
        print(f"Błąd zapisywania wyniku bitwy: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/simulation-step", methods=["GET"])
def simulation_step():
    global simulation, simulation_running

    with simulation_lock:
        if simulation is None:
            return jsonify({"error": "Symulacja nie została rozpoczęta"}), 400

        if simulation_running:
            print(f"Executing step... Agents: {len(simulation.schedule.agents)}")
            simulation.step()

        agents_data = []
        for agent in simulation.schedule.agents:
            if agent.hp <= 0:
                continue

            pos = agent.get_pos_tuple()
            agents_data.append(
                {
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
                    "sprite_path": simulation.unit_params[agent.unit_type][
                        "sprite_path"
                    ],
                }
            )

        stats = {
            "crown_count": len(
                [
                    a
                    for a in simulation.schedule.agents
                    if a.faction == "Armia Koronna" and a.hp > 0
                ]
            ),
            "cossack_count": len(
                [
                    a
                    for a in simulation.schedule.agents
                    if a.faction == "Kozacy/Tatarzy" and a.hp > 0
                ]
            ),
            "total_agents": len([a for a in simulation.schedule.agents if a.hp > 0]),
        }

        battle_status = simulation.get_battle_status()

        healing_zones_data = [{"x": x, "y": y} for x, y in simulation.healing_tiles]

        return jsonify(
            {
                "agents": agents_data,
                "stats": stats,
                "battle_status": battle_status,
                "running": simulation_running,
                "map_width": simulation.grid.width,
                "map_height": simulation.grid.height,
                "healing_zones": healing_zones_data,
            }
        )


@app.route("/api/simulation-frame", methods=["GET"])
def get_simulation_frame():
    global simulation

    if simulation is None:
        return jsonify({"error": "Symulacja nie została rozpoczęta"}), 400

    with simulation_lock:
        renderer = WebRenderer(simulation)
        frame = renderer.render_frame()

        buffered = io.BytesIO()
        frame.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return jsonify(
            {"frame": f"data:image/png;base64,{img_str}", "running": simulation_running}
        )


def stream_simulation():
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

            yield (
                b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + img_bytes + b"\r\n"
            )

            time.sleep(0.2)
        else:
            time.sleep(0.1)


@app.route("/api/video-feed")
def video_feed():
    return Response(
        stream_simulation(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/api/map-image")
def get_map_image():
    try:
        global simulation

        model_to_render = simulation
        if model_to_render is None:
            model_to_render = BattleOfZborowModel(MAP_PATH, {})

        renderer = WebRenderer(model_to_render, scale=1)
        image = renderer.render_map_only()

        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return jsonify(
            {
                "image": f"data:image/png;base64,{img_str}",
                "width": renderer.width,
                "height": renderer.height,
            }
        )
    except Exception as e:
        print(f"Błąd generowania obrazu mapy: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/heatmap-image/<result_id>", methods=["GET"])
def get_heatmap_image(result_id):
    try:
        if not os.path.exists(RESULTS_FILE):
            return jsonify({"error": "No results file"}), 404

        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        result = next((item for item in data if item.get("id") == result_id), None)

        if not result or not result.get("heatmap"):
            return jsonify({"error": "Result or heatmap data not found"}), 404

        heatmap_data = result["heatmap"]

        global simulation
        model_to_render = simulation
        if model_to_render is None:
            model_to_render = BattleOfZborowModel(MAP_PATH, {})

        renderer = WebRenderer(model_to_render, scale=1)

        image = renderer.render_heatmap(heatmap_data)

        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return jsonify(
            {
                "image": f"data:image/png;base64,{img_str}",
                "width": renderer.width,
                "height": renderer.height,
            }
        )

    except Exception as e:
        print(f"Błąd generowania obrazu heatmapy: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
