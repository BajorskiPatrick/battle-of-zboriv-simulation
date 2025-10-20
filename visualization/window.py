import arcade
from simulation.model import BattleOfZborowModel
from .sprites import AgentSprite

MAP_PATH = "assets/map/zborow_battlefield.tmx"

class SimulationWindow(arcade.Window):
    """ Główne okno wizualizacji Arcade. """
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        arcade.set_background_color(arcade.color.BLACK)
        
        self.model = BattleOfZborowModel(MAP_PATH)
        self.tile_map = None
        self.agent_sprites = arcade.SpriteList()
        self.tile_size = 16 # Dopasuj do rozmiaru kafelka w Tiled
        self.sprite_map = {} # Mapa agent_id -> sprite

    def setup(self):
        """ Konfiguracja sceny. """
        self.tile_map = arcade.load_tilemap(MAP_PATH, scaling=1.0)
        
        for agent in self.model.schedule.agents:
            sprite = AgentSprite(agent)
            sprite.center_x = (agent.pos[0] + 0.5) * self.tile_size
            sprite.center_y = (self.model.height - agent.pos[1] - 0.5) * self.tile_size
            self.agent_sprites.append(sprite)
            self.sprite_map[agent.unique_id] = sprite
    
    def on_draw(self):
        """ Rysowanie sceny. """
        self.clear()
        self.tile_map.sprite_lists["Teren"].draw()
        # Narysuj inne warstwy, jeśli istnieją
        self.agent_sprites.draw()
        for sprite in self.agent_sprites:
            sprite.draw_health_bar()

    def on_update(self, delta_time):
        """ Logika aktualizacji. """
        self.model.step()
        
        # Usuń sprajty dla usuniętych agentów
        current_agent_ids = {agent.unique_id for agent in self.model.schedule.agents}
        sprites_to_remove = [sprite for sprite in self.agent_sprites if sprite.agent.unique_id not in current_agent_ids]
        for sprite in sprites_to_remove:
            sprite.remove_from_sprite_lists()
            del self.sprite_map[sprite.agent.unique_id]
        
        # Zaktualizuj pozycje istniejących sprajtów
        for agent in self.model.schedule.agents:
            sprite = self.sprite_map.get(agent.unique_id)
            if sprite:
                target_x = (agent.pos[0] + 0.5) * self.tile_size
                target_y = (self.model.height - agent.pos[1] - 0.5) * self.tile_size
                
                # Płynne przejście do nowej pozycji
                sprite.center_x += (target_x - sprite.center_x) * 0.2
                sprite.center_y += (target_y - sprite.center_y) * 0.2