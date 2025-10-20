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
        BAR_WIDTH = 24
        BAR_HEIGHT = 4

        # --- Pasek zdrowia (na dole) ---
        health_y = self.center_y + 14
        health_width_current = BAR_WIDTH * (self.agent.hp / self.agent.max_hp)
        
        # Tło paska (czerwone)
        arcade.draw_lrbt_rectangle_filled(
            left=self.center_x - BAR_WIDTH / 2,
            right=self.center_x + BAR_WIDTH / 2,
            top=health_y + BAR_HEIGHT / 2,
            bottom=health_y - BAR_HEIGHT / 2,
            color=arcade.color.RED
        )
        # Wypełnienie paska (zielone)
        if health_width_current > 0:
            arcade.draw_lrbt_rectangle_filled(
                left=self.center_x - BAR_WIDTH / 2,
                right=self.center_x - BAR_WIDTH / 2 + health_width_current,
                top=health_y + BAR_HEIGHT / 2,
                bottom=health_y - BAR_HEIGHT / 2,
                color=arcade.color.GREEN
            )

        # --- Pasek morale (na górze) ---
        morale_y = self.center_y + 20
        morale_width_current = BAR_WIDTH * (self.agent.morale / self.agent.max_morale)
        
        # Tło paska (ciemnoszare)
        arcade.draw_lrbt_rectangle_filled(
            left=self.center_x - BAR_WIDTH / 2,
            right=self.center_x + BAR_WIDTH / 2,
            top=morale_y + BAR_HEIGHT / 2,
            bottom=morale_y - BAR_HEIGHT / 2,
            color=arcade.color.DARK_GRAY
        )
        # Wypełnienie paska (niebieskie)
        if morale_width_current > 0:
            arcade.draw_lrbt_rectangle_filled(
                left=self.center_x - BAR_WIDTH / 2,
                right=self.center_x - BAR_WIDTH / 2 + morale_width_current,
                top=morale_y + BAR_HEIGHT / 2,
                bottom=morale_y - BAR_HEIGHT / 2,
                color=arcade.color.CYAN
            )