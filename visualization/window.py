import arcade
from simulation.model import BattleOfZborowModel
from visualization.sprites import AgentSprite

# --- Stałe konfiguracyjne ---
MAP_PATH = "assets/map/zborow_battlefield.tmx"
SIMULATION_TICKS_PER_SECOND = 5.0  # Kontroluje prędkość logiki symulacji (5 kroków na sekundę)

class SimulationWindow(arcade.Window):
    """ Główne okno wizualizacji Arcade. """

    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        arcade.set_background_color(arcade.color.BLACK_OLIVE)

        self.model = BattleOfZborowModel(MAP_PATH)
        self.tile_map = None
        self.agent_sprites = arcade.SpriteList()
        self.tile_size = 16  # Dopasuj do rozmiaru kafelka w Tiled
        self.sprite_map = {}  # Słownik mapujący ID agenta na jego sprajt
        self.time_since_last_tick = 0.0  # Licznik czasu do kontroli prędkości symulacji

    def setup(self):
        """ Konfiguracja sceny, ładowanie mapy i tworzenie sprajtów. """
        self.tile_map = arcade.load_tilemap(MAP_PATH, scaling=1.0)

        # Stwórz sprajty dla wszystkich agentów z modelu
        for agent in self.model.schedule.agents:
            sprite = AgentSprite(agent)
            
            # Pobierz pozycję początkową jako krotkę
            agent_pos_tuple = agent.get_pos_tuple()

            # Ustaw pozycję sprajta na ekranie (z uwzględnieniem odwróconej osi Y)
            sprite.center_x = (agent_pos_tuple[0] + 0.5) * self.tile_size
            sprite.center_y = (self.model.height - agent_pos_tuple[1] - 0.5) * self.tile_size
            
            self.agent_sprites.append(sprite)
            self.sprite_map[agent.unique_id] = sprite

    def on_draw(self):
        """ Rysowanie całej sceny. """
        self.clear()
        
        # Rysowanie warstw mapy
        if self.tile_map.sprite_lists.get("Teren"):
            self.tile_map.sprite_lists["Teren"].draw()
        
        # Rysowanie sprajtów agentów
        self.agent_sprites.draw()

        # Rysowanie pasków zdrowia/morale nad każdym sprajtem
        for sprite in self.agent_sprites:
            sprite.draw_health_bar()

    def on_update(self, delta_time):
        """ Logika aktualizacji wywoływana w każdej klatce. """
        
        # Timer spowalniający logikę symulacji
        self.time_since_last_tick += delta_time
        if self.time_since_last_tick >= 1.0 / SIMULATION_TICKS_PER_SECOND:
            self.model.step()
            self.time_since_last_tick = 0.0

        # Synchronizacja wizualizacji z modelem
        
        # 1. Usuń sprajty dla agentów, którzy zginęli
        current_agent_ids = {agent.unique_id for agent in self.model.schedule.agents}
        sprites_to_remove = [sprite for sprite in self.agent_sprites if sprite.agent.unique_id not in current_agent_ids]
        for sprite in sprites_to_remove:
            sprite.remove_from_sprite_lists()
            if sprite.agent.unique_id in self.sprite_map:
                del self.sprite_map[sprite.agent.unique_id]

        # 2. Zaktualizuj pozycje istniejących sprajtów
        for agent in self.model.schedule.agents:
            sprite = self.sprite_map.get(agent.unique_id)
            if sprite:
                agent_pos_tuple = agent.get_pos_tuple()
                
                # Oblicz docelową pozycję sprajta na ekranie
                target_x = (agent_pos_tuple[0] + 0.5) * self.tile_size
                target_y = (self.model.height - agent_pos_tuple[1] - 0.5) * self.tile_size
                
                # Płynne animowanie przejścia do nowej pozycji
                sprite.center_x += (target_x - sprite.center_x) * 0.2
                sprite.center_y += (target_y - sprite.center_y) * 0.2