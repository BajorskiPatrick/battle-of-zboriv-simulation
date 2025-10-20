import arcade

# --- Ścieżki do sprajtów ---
CROWN_SPRITE = "assets/sprites/crown_infantry.png"
COSSACK_SPRITE = "assets/sprites/cossack_cavalry.png"

class AgentSprite(arcade.Sprite):
    """ Rozszerzona klasa Sprite do reprezentacji agenta z paskiem zdrowia/morale. """
    def __init__(self, agent):
        self.agent = agent
        
        # Wybierz odpowiednią grafikę na podstawie frakcji
        sprite_path = agent.model.unit_params[agent.unit_type]["sprite_path"]
        super().__init__(sprite_path, scale=0.8)

    def draw_health_bar(self):
        """ Rysuje pasek zdrowia i morale nad sprajtem. """
        # Pasek zdrowia (zielony)
        health_width = 20 * (self.agent.hp / self.agent.max_hp)
        arcade.draw_rectangle_filled(self.center_x, self.center_y + 12, 20, 4, arcade.color.RED)
        if health_width > 0:
            arcade.draw_rectangle_filled(self.center_x - (20 - health_width) / 2, self.center_y + 12, health_width, 4, arcade.color.GREEN)

        # Pasek morale (niebieski)
        morale_width = 20 * (self.agent.morale / self.agent.max_morale)
        arcade.draw_rectangle_filled(self.center_x, self.center_y + 18, 20, 4, arcade.color.DARK_GRAY)
        if morale_width > 0:
            arcade.draw_rectangle_filled(self.center_x - (20 - morale_width) / 2, self.center_y + 18, morale_width, 4, arcade.color.CYAN)