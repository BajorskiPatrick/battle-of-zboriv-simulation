import mesa
import pytmx
import numpy as np
from .agent import MilitaryAgent
from pathfinding.core.grid import Grid


class BattleOfZborowModel(mesa.Model):
    def __init__(self, map_file_path, units_config=None, weather="clear"):
        super().__init__()
        self.weather = weather
        self.schedule = mesa.time.RandomActivation(self)

        self.map_data = pytmx.TiledMap(map_file_path)
        self.width = self.map_data.width
        self.height = self.map_data.height

        self.grid = mesa.space.MultiGrid(self.width, self.height, torus=False)

        self.terrain_costs = np.array(self.load_terrain_data(), dtype=np.float32)

        self.apply_weather_effects()

        self.path_grid = Grid(matrix=self.terrain_costs.tolist())

        self.heatmap_crown = np.zeros((self.height, self.width), dtype=int)
        self.heatmap_cossack = np.zeros((self.height, self.width), dtype=int)

        self.units_config = units_config if units_config else {}

        self.healing_centers = [
            (73, 24),
            (126, 24),
            (127, 41),
            (127, 52),
            (99, 68),
            (127, 67),
        ]

        self.healing_tiles = []
        for center in self.healing_centers:
            cx, cy = center
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    x, y = cx + dx, cy + dy
                    if 0 <= x < self.width and 0 <= y < self.height:
                        self.healing_tiles.append((x, y))

        self.find_healing_entrances()


        self.unit_params = {
            "Husaria": {
                "hp": 150,
                "morale": 140,
                "discipline": 95,
                "melee_damage": 100,
                "ranged_damage": 0,
                "range": 1,
                "ammo": 0,
                "defense": 8,
                "speed": 6,
                "rate_of_fire": 1.0,
                "description": "Elitarna ciężka jazda przełamująca.",
                "sprite_path": "assets/sprites/crown_cavalry.png",
            },
            "Pancerni": {
                "hp": 120,
                "morale": 110,
                "discipline": 85,
                "melee_damage": 70,
                "ranged_damage": 0,
                "range": 1,
                "ammo": 0,
                "defense": 5,
                "speed": 7,
                "rate_of_fire": 1.0,
                "description": "Jazda średniozbrojna, uniwersalna.",
                "sprite_path": "assets/sprites/pancerni.png",
            },
            "Rajtaria": {
                "hp": 110,
                "morale": 100,
                "discipline": 90,
                "melee_damage": 40,
                "ranged_damage": 30,
                "range": 3,
                "ammo": 12,
                "defense": 6,
                "speed": 6,
                "rate_of_fire": 0.8,
                "description": "Ciężka jazda z bronią palną.",
                "sprite_path": "assets/sprites/rajtaria.png",
            },
            "Dragonia": {
                "hp": 100,
                "morale": 95,
                "discipline": 85,
                "melee_damage": 30,
                "ranged_damage": 25,
                "range": 4,
                "ammo": 15,
                "defense": 4,
                "speed": 5,
                "rate_of_fire": 1.2,
                "description": "Mobilna piechota konna.",
                "sprite_path": "assets/sprites/crown_dragoon.png",
            },
            "Piechota Niemiecka": {
                "hp": 110,
                "morale": 100,
                "discipline": 95,
                "melee_damage": 25,
                "ranged_damage": 35,
                "range": 5,
                "ammo": 20,
                "defense": 6,
                "speed": 3,
                "rate_of_fire": 1.3,
                "description": "Wysoka dyscyplina, silny ogień.",
                "sprite_path": "assets/sprites/crown_infantry.png",
            },
            "Pospolite Ruszenie": {
                "hp": 90,
                "morale": 50,
                "discipline": 20,
                "melee_damage": 20,
                "ranged_damage": 10,
                "range": 2,
                "ammo": 5,
                "defense": 2,
                "speed": 6,
                "rate_of_fire": 0.8,
                "description": "Niska dyscyplina, podatność na panikę.",
                "sprite_path": "assets/sprites/crown_levy.png",
            },
            "Czeladz Obozowa": {
                "hp": 60,
                "morale": 90,
                "discipline": 40,
                "melee_damage": 25,
                "ranged_damage": 0,
                "range": 1,
                "ammo": 0,
                "defense": 0,
                "speed": 5,
                "rate_of_fire": 1.0,
                "description": "Słabo uzbrojona, zdeterminowana.",
                "sprite_path": "assets/sprites/crown_levy.png",
            },
            "Artyleria Koronna": {
                "hp": 50,
                "morale": 90,
                "discipline": 90,
                "melee_damage": 5,
                "ranged_damage": 150,
                "range": 15,
                "ammo": 30,
                "defense": 0,
                "speed": 1,
                "rate_of_fire": 0.25,
                "description": "Potężna siła ognia, bardzo wolna.",
                "sprite_path": "assets/sprites/armata.png",
            },
            "Jazda Tatarska": {
                "hp": 85,
                "morale": 80,
                "discipline": 70,
                "melee_damage": 30,
                "ranged_damage": 15,
                "range": 6,
                "ammo": 40,
                "defense": 1,
                "speed": 9,
                "rate_of_fire": 1.8,
                "description": "Szybcy łucznicy.",
                "sprite_path": "assets/sprites/cossack_cavalry.png",
            },
            "Piechota Kozacka": {
                "hp": 115,
                "morale": 110,
                "discipline": 90,
                "melee_damage": 35,
                "ranged_damage": 35,
                "range": 5,
                "ammo": 25,
                "defense": 3,
                "speed": 4,
                "rate_of_fire": 1.4,
                "description": "Znakomici strzelcy.",
                "sprite_path": "assets/sprites/cossack_infantry.png",
            },
            "Czern": {
                "hp": 70,
                "morale": 60,
                "discipline": 40,
                "melee_damage": 20,
                "ranged_damage": 0,
                "range": 1,
                "ammo": 0,
                "defense": 0,
                "speed": 5,
                "rate_of_fire": 1.0,
                "description": "Liczni, słabo uzbrojeni.",
                "sprite_path": "assets/sprites/cossack_infantry.png",
            },
            "Jazda Kozacka": {
                "hp": 100,
                "morale": 90,
                "discipline": 75,
                "melee_damage": 50,
                "ranged_damage": 0,
                "range": 2,
                "ammo": 0,
                "defense": 3,
                "speed": 7,
                "rate_of_fire": 1.0,
                "description": "Jazda średnia.",
                "sprite_path": "assets/sprites/cossack_cavalry.png",
            },
            "Artyleria Kozacka": {
                "hp": 40,
                "morale": 80,
                "discipline": 80,
                "melee_damage": 5,
                "ranged_damage": 130,
                "range": 14,
                "ammo": 25,
                "defense": 0,
                "speed": 1,
                "rate_of_fire": 0.25,
                "description": "Ostrzał obozu.",
                "sprite_path": "assets/sprites/cossack_infantry.png",
            },
        }

        self.apply_weather_to_units()

        self.setup_agents()

    def find_healing_entrances(self):
        self.healing_entrances = {}
        found_entrances = []

        try:
            terrain_layer = self.map_data.get_layer_by_name("Teren")
            if terrain_layer:
                for x, y, gid in terrain_layer.iter_data():
                    if gid != 0:
                        props = self.map_data.get_tile_properties_by_gid(gid)
                        if props and props.get("healing_zone_entry"):
                            found_entrances.append((x, y))
        except Exception as e:
            print(f"Error finding healing entrances: {e}")

        for center in self.healing_centers:
            if found_entrances:
                closest = min(found_entrances, key=lambda e: max(abs(e[0]-center[0]), abs(e[1]-center[1])))
                if max(abs(closest[0]-center[0]), abs(closest[1]-center[1])) <= 2:
                    self.healing_entrances[center] = closest
                else:
                    self.healing_entrances[center] = (center[0], center[1] + 1)
            else:
                self.healing_entrances[center] = (center[0], center[1] + 1)

    def get_healing_entrance(self, center):
        return self.healing_entrances.get(center)

    def load_terrain_data(self):
        costs = np.ones((self.height, self.width), dtype=np.float32)
        try:
            terrain_layer = self.map_data.get_layer_by_name("Teren")
            if terrain_layer:
                for x, y, gid in terrain_layer.iter_data():
                    if gid != 0:
                        props = self.map_data.get_tile_properties_by_gid(gid)
                        if props and "movement_cost" in props:
                            costs[y][x] = props["movement_cost"]
        except Exception as e:
            print(f"Błąd ładowania terenu: {e}. Używam domyślnych kosztów.")
        return costs

    def apply_weather_effects(self):
        if self.weather == "rain":
            print("🌧️ POGODA: Deszcz - teren zmienia się w błoto.")
            self.terrain_costs = np.where(
                self.terrain_costs == 1.5, self.terrain_costs * 2.5, self.terrain_costs
            )
        elif self.weather == "fog":
            print("🌫️ POGODA: Mgła - ograniczona widoczność.")

    def apply_weather_to_units(self):
        if self.weather == "rain":
            for name, params in self.unit_params.items():
                if params["ranged_damage"] > 0:
                    params["ranged_damage"] = int(params["ranged_damage"] * 0.3)
                    params["description"] += " (Mokry proch/cięciwy!)"

                if any(x in name for x in ["Jazda", "Husaria", "Pancerni", "Rajtaria"]):
                    params["speed"] = max(2, params["speed"] - 3)
                if "Artyleria" in name:
                    params["speed"] = 1

                if params.get("rate_of_fire"):
                    params["rate_of_fire"] = max(0.1, params["rate_of_fire"] * 0.8)

    def find_valid_spawn_position(self, y_min, y_max, max_attempts=75):
        x_left, x_right = 5, max(6, self.width - 5)
        y_low, y_high = max(0, y_min), min(self.height - 1, y_max)

        for _ in range(max_attempts):
            x = self.random.randrange(x_left, x_right)
            y = self.random.randrange(y_low, y_high)
            try:
                if self.terrain_costs[y][x] >= 5:
                    continue
            except:
                continue

            if not self.grid.is_cell_empty((x, y)):
                continue
            return (x, y)
        return (
            self.random.randrange(x_left, x_right),
            self.random.randrange(y_low, y_high),
        )

    def setup_agents(self):
        deployment_zones = self.units_config.get("_deployment", None)
        units_to_spawn = {
            k: v for k, v in self.units_config.items() if k != "_deployment"
        }

        if not units_to_spawn:
            return

        for unit_type, count in units_to_spawn.items():
            if unit_type not in self.unit_params:
                continue

            if unit_type in [
                "Jazda Tatarska",
                "Piechota Kozacka",
                "Czern",
                "Jazda Kozacka",
                "Artyleria Kozacka",
            ]:
                faction = "Kozacy/Tatarzy"
            else:
                faction = "Armia Koronna"

            zone = deployment_zones.get(unit_type) if deployment_zones else None

            for _ in range(count):
                if zone:
                    pos = self.find_valid_spawn_in_zone(zone)
                else:
                    if faction == "Kozacy/Tatarzy":
                        pos = self.find_valid_spawn_position(1, 20)
                    else:
                        pos = self.find_valid_spawn_position(
                            self.height - 20, self.height - 2
                        )

                agent = MilitaryAgent(self.next_id(), self, faction, unit_type)
                self.grid.place_agent(agent, pos)
                self.schedule.add(agent)

    def find_valid_spawn_in_zone(self, zone, max_attempts=50):
        x_min, x_max = zone.get("x", [0, self.width - 1])
        y_min, y_max = zone.get("y", [0, self.height - 1])
        x_min, x_max = max(0, x_min), min(self.width - 1, x_max)
        y_min, y_max = max(0, y_min), min(self.height - 1, y_max)

        for _ in range(max_attempts):
            x = self.random.randint(x_min, x_max)
            y = self.random.randint(y_min, y_max)
            if not self.grid.is_cell_empty((x, y)):
                continue
            if self.terrain_costs[y][x] >= 5:
                continue
            return (x, y)
        return (x_min, y_min)

    def step(self):
        self.schedule.step()

        for agent in self.schedule.agents:
            if isinstance(agent, MilitaryAgent) and agent.hp > 0 and agent.pos:
                x, y = agent.pos
                if 0 <= x < self.width and 0 <= y < self.height:
                    if agent.faction == "Armia Koronna":
                        self.heatmap_crown[y][x] += 1
                    else:
                        self.heatmap_cossack[y][x] += 1

        self.cleanup_dead_agents()
        self.apply_camp_healing()

    def is_zone_full(self, center):
        cx, cy = center
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                x, y = cx + dx, cy + dy
                if 0 <= x < self.width and 0 <= y < self.height:
                    cell_contents = self.grid.get_cell_list_contents([(x, y)])
                    if not any(isinstance(a, MilitaryAgent) for a in cell_contents):
                        return False
        return True

    def apply_camp_healing(self):
        for tile in self.healing_tiles:
            cell_contents = self.grid.get_cell_list_contents([tile])

            for agent in cell_contents:
                    if (
                        isinstance(agent, MilitaryAgent)
                        and agent.faction == "Armia Koronna"
                        and agent.hp > 0
                    ):

                        if agent.hp < agent.max_hp:
                            heal_amount = 5
                            agent.hp = min(agent.max_hp, agent.hp + heal_amount)

                        if agent.morale < agent.max_morale:
                            morale_boost = 3
                            agent.morale = min(
                                agent.max_morale, agent.morale + morale_boost
                            )

                        if (
                            agent.state == "FLEEING"
                            and agent.hp > agent.max_hp * 0.6
                            and agent.morale > agent.max_morale * 0.6
                        ):
                            agent.state = "IDLE"
                            agent.path = []

    def cleanup_dead_agents(self):
        dead_agents = [
            agent
            for agent in self.schedule.agents
            if isinstance(agent, MilitaryAgent) and agent.hp <= 0
        ]
        for agent in dead_agents:
            if agent.pos:
                self.grid.remove_agent(agent)
            if agent in self.schedule.agents:
                self.schedule.remove(agent)

    def get_battle_status(self):
        self.cleanup_dead_agents()
        crown_count = sum(
            1
            for a in self.schedule.agents
            if isinstance(a, MilitaryAgent)
            and a.faction == "Armia Koronna"
            and a.hp > 0
        )
        cossack_count = sum(
            1
            for a in self.schedule.agents
            if isinstance(a, MilitaryAgent)
            and a.faction == "Kozacy/Tatarzy"
            and a.hp > 0
        )

        if crown_count == 0 and cossack_count > 0:
            return {
                "status": "finished",
                "winner": "Kozacy/Tatarzy",
                "survivors": cossack_count,
            }
        elif cossack_count == 0 and crown_count > 0:
            return {
                "status": "finished",
                "winner": "Armia Koronna",
                "survivors": crown_count,
            }
        elif crown_count == 0 and cossack_count == 0:
            return {"status": "finished", "winner": "Remis", "survivors": 0}
        else:
            return {
                "status": "ongoing",
                "crown_count": crown_count,
                "cossack_count": cossack_count,
            }
