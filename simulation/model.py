import mesa
import pytmx
import numpy as np
from .agent import MilitaryAgent
from pathfinding.core.grid import Grid

class BattleOfZborowModel(mesa.Model):
    """ Główny model symulacji bitwy. """
    def __init__(self, map_file_path, units_config=None):
        super().__init__()
        self.schedule = mesa.time.RandomActivation(self)
        
        # Wczytaj mapę i jej właściwości
        self.map_data = pytmx.TiledMap(map_file_path)
        self.width = self.map_data.width
        self.height = self.map_data.height
        
        self.grid = mesa.space.MultiGrid(self.width, self.height, torus=False)
        self.terrain_costs = self.load_terrain_data()
        self.path_grid = Grid(matrix=self.terrain_costs)
        
        # Konfiguracja jednostek z interfejsu webowego
        self.units_config = units_config if units_config else {}

        self.unit_params = {
            # --- ARMIA KORONNA ---
            "Piechota": {
                "hp": 120, "morale": 100, "range": 5, "damage": 10, "speed": 1,
                "description": "Wysoka dyscyplina, odporność na szarże.",
                "sprite_path": "assets/sprites/crown_infantry.png"
            },
            "Dragonia": {
                "hp": 90, "morale": 85, "range": 6, "damage": 8, "speed": 2,
                "description": "Mobilna, może walczyć pieszo.",
                "sprite_path": "assets/sprites/crown_dragoon.png"
            },
            "Jazda": {
                "hp": 100, "morale": 90, "range": 1, "damage": 20, "speed": 3,
                "description": "Wysoka prędkość, potężny bonus do szarży.",
                "sprite_path": "assets/sprites/crown_cavalry.png"
            },
            "Pospolite Ruszenie": {
                "hp": 70, "morale": 40, "range": 2, "damage": 7, "speed": 2,
                "description": "Niskie morale, podatność na panikę.",
                "sprite_path": "assets/sprites/crown_levy.png"
            },

            # --- KOZACY I TATARZY ---
            "Piechota Kozacka": {
                "hp": 100, "morale": 110, "range": 5, "damage": 12, "speed": 1,
                "description": "Wysoka determinacja, szybsze ładowanie.",
                "sprite_path": "assets/sprites/cossack_infantry.png"
            },
            "Jazda Tatarska": {
                "hp": 80, "morale": 80, "range": 7, "damage": 9, "speed": 4,
                "description": "Najwyższa mobilność i szybkostrzelność, niezawodna w deszczu.",
                "sprite_path": "assets/sprites/cossack_cavalry.png"
            }
        }

        # Stwórz agentów (scenariusz początkowy)
        self.setup_agents()

    def load_terrain_data(self):
        """ Wczytuje dane o terenie z mapy Tiled do macierzy kosztów. """
        costs = np.ones((self.height, self.width), dtype=np.float32)
        
        try:
            terrain_layer = self.map_data.get_layer_by_name("Teren")
            if terrain_layer:
                for x, y, gid in terrain_layer.iter_data():
                    if gid != 0:
                        props = self.map_data.get_tile_properties_by_gid(gid)
                        if props and 'movement_cost' in props:
                            costs[y][x] = props['movement_cost']
        except Exception as e:
            print(f"Uwaga: Nie można załadować warstwy terenu: {e}")
            print("Używam domyślnych kosztów ruchu (wszystkie = 1)")
        
        return costs.tolist()


    def setup_agents(self):
        """ Tworzy i rozmieszcza agentów na mapie w zorganizowanych strefach. """
        
        # Jeśli nie ma konfiguracji, użyj domyślnego scenariusza
        if not self.units_config:
            self._setup_default_scenario()
            return
        
        # Twórz jednostki zgodnie z konfiguracją użytkownika
        for unit_type, count in self.units_config.items():
            # Określ frakcję na podstawie nazwy jednostki
            if "Kozacka" in unit_type or "Tatarska" in unit_type:
                faction = "Kozacy/Tatarzy"
                # Rozmieszczenie na górze mapy
                for i in range(count):
                    x = self.random.randrange(10, self.width - 10)
                    y = self.random.randrange(1, 15)
                    agent = MilitaryAgent(self.next_id(), self, faction, unit_type)
                    self.grid.place_agent(agent, (x, y))
                    self.schedule.add(agent)
            else:
                faction = "Armia Koronna"
                # Rozmieszczenie na dole mapy
                for i in range(count):
                    x = self.random.randrange(10, self.width - 10)
                    y = self.random.randrange(self.height - 15, self.height - 1)
                    agent = MilitaryAgent(self.next_id(), self, faction, unit_type)
                    self.grid.place_agent(agent, (x, y))
                    self.schedule.add(agent)
    
    def _setup_default_scenario(self):
        """ Domyślny scenariusz początkowy (używany w trybie desktop). """
        # Armia Koronna (na dole mapy) - 5x Piechota, 3x Jazda
        for i in range(5):
            x = self.random.randrange(10, self.width - 10)
            y = self.random.randrange(self.height - 10, self.height - 1)
            agent = MilitaryAgent(self.next_id(), self, "Armia Koronna", "Piechota")
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)
        for i in range(3):
            x = self.random.randrange(5, self.width - 5)
            y = self.random.randrange(self.height - 15, self.height - 5)
            agent = MilitaryAgent(self.next_id(), self, "Armia Koronna", "Jazda")
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)

        # Kozacy i Tatarzy (na górze mapy) - 5x Piechota Kozacka, 5x Jazda Tatarska
        for i in range(5):
            x = self.random.randrange(10, self.width - 10)
            y = self.random.randrange(1, 10)
            agent = MilitaryAgent(self.next_id(), self, "Kozacy/Tatarzy", "Piechota Kozacka")
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)
        for i in range(5):
            x = self.random.randrange(5, self.width - 5)
            y = self.random.randrange(1, 15)
            agent = MilitaryAgent(self.next_id(), self, "Kozacy/Tatarzy", "Jazda Tatarska")
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)

    def step(self):
        """ Wykonuje jeden krok symulacji. """
        self.schedule.step()