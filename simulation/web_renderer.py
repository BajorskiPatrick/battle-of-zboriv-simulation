from PIL import Image, ImageDraw, ImageFont
import os

class WebRenderer:
    """Renderer do generowania obrazów symulacji dla interfejsu webowego."""
    
    def __init__(self, model, tile_size=16, scale=2):
        self.model = model
        self.tile_size = tile_size
        self.scale = scale  # Skalowanie dla lepszej widoczności w przeglądarce
        self.width = model.width * tile_size * scale
        self.height = model.height * tile_size * scale
        
        # Cache dla sprite'ów
        self.sprite_cache = {}
        
    def load_sprite(self, sprite_path):
        """Ładuje i cache'uje sprite."""
        if sprite_path in self.sprite_cache:
            return self.sprite_cache[sprite_path]
        
        try:
            if os.path.exists(sprite_path):
                sprite = Image.open(sprite_path).convert("RGBA")
                # Skaluj sprite do odpowiedniego rozmiaru
                new_size = int(self.tile_size * self.scale * 0.8)
                sprite = sprite.resize((new_size, new_size), Image.Resampling.LANCZOS)
                self.sprite_cache[sprite_path] = sprite
                return sprite
        except Exception as e:
            print(f"Błąd ładowania sprite: {sprite_path}, {e}")
        
        # Fallback - kolorowy kwadrat
        return self._create_fallback_sprite()
    
    def _create_fallback_sprite(self):
        """Tworzy prosty sprite zastępczy."""
        size = int(self.tile_size * self.scale * 0.8)
        sprite = Image.new("RGBA", (size, size), (100, 100, 100, 255))
        return sprite
    
    def render_frame(self):
        """Renderuje aktualny stan symulacji jako obraz."""
        # Tło - zielone pole bitwy
        image = Image.new("RGB", (self.width, self.height), (34, 139, 34))
        draw = ImageDraw.Draw(image)
        
        # Rysuj siatkę (opcjonalnie)
        grid_color = (50, 150, 50)
        for x in range(0, self.width, self.tile_size * self.scale):
            draw.line([(x, 0), (x, self.height)], fill=grid_color, width=1)
        for y in range(0, self.height, self.tile_size * self.scale):
            draw.line([(0, y), (self.width, y)], fill=grid_color, width=1)
        
        # Rysuj strefy startowe (półprzezroczyste)
        overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Strefa Koronna (dół - czerwonawa)
        crown_zone_y = (self.model.height - 15) * self.tile_size * self.scale
        overlay_draw.rectangle(
            [0, crown_zone_y, self.width, self.height],
            fill=(200, 50, 50, 30)
        )
        
        # Strefa Kozacy/Tatarzy (góra - niebieska)
        cossack_zone_y = 15 * self.tile_size * self.scale
        overlay_draw.rectangle(
            [0, 0, self.width, cossack_zone_y],
            fill=(50, 50, 200, 30)
        )
        
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
        
        # Rysuj jednostki
        for agent in self.model.schedule.agents:
            pos = agent.get_pos_tuple()
            
            # Pozycja na obrazie (odwrócona oś Y)
            x = int((pos[0] + 0.5) * self.tile_size * self.scale)
            y = int((self.model.height - pos[1] - 0.5) * self.tile_size * self.scale)
            
            # Wczytaj i narysuj sprite
            sprite = self.load_sprite(agent.model.unit_params[agent.unit_type]["sprite_path"])
            sprite_x = x - sprite.width // 2
            sprite_y = y - sprite.height // 2
            
            # Narysuj sprite
            image.paste(sprite, (sprite_x, sprite_y), sprite)
            
            # Rysuj paski HP i morale
            self._draw_health_bars(image, x, y, agent)
        
        return image
    
    def _draw_health_bars(self, image, x, y, agent):
        """Rysuje paski HP i morale nad jednostką."""
        draw = ImageDraw.Draw(image)
        
        bar_width = int(24 * self.scale)
        bar_height = int(4 * self.scale)
        
        # Pasek HP (dolny)
        hp_y = y - int(14 * self.scale)
        hp_percent = agent.hp / agent.max_hp
        
        # Tło (czerwone)
        draw.rectangle(
            [x - bar_width // 2, hp_y - bar_height // 2,
             x + bar_width // 2, hp_y + bar_height // 2],
            fill=(200, 0, 0)
        )
        
        # Wypełnienie (zielone)
        if hp_percent > 0:
            hp_fill_width = int(bar_width * hp_percent)
            draw.rectangle(
                [x - bar_width // 2, hp_y - bar_height // 2,
                 x - bar_width // 2 + hp_fill_width, hp_y + bar_height // 2],
                fill=(0, 200, 0)
            )
        
        # Pasek morale (górny)
        morale_y = y - int(20 * self.scale)
        morale_percent = agent.morale / agent.max_morale
        
        # Tło (ciemnoszare)
        draw.rectangle(
            [x - bar_width // 2, morale_y - bar_height // 2,
             x + bar_width // 2, morale_y + bar_height // 2],
            fill=(100, 100, 100)
        )
        
        # Wypełnienie (cyan)
        if morale_percent > 0:
            morale_fill_width = int(bar_width * morale_percent)
            draw.rectangle(
                [x - bar_width // 2, morale_y - bar_height // 2,
                 x - bar_width // 2 + morale_fill_width, morale_y + bar_height // 2],
                fill=(0, 200, 200)
            )
        
        # Ramka wokół pasków
        draw.rectangle(
            [x - bar_width // 2 - 1, hp_y - bar_height // 2 - 1,
             x + bar_width // 2 + 1, hp_y + bar_height // 2 + 1],
            outline=(0, 0, 0), width=1
        )
        draw.rectangle(
            [x - bar_width // 2 - 1, morale_y - bar_height // 2 - 1,
             x + bar_width // 2 + 1, morale_y + bar_height // 2 + 1],
            outline=(0, 0, 0), width=1
        )
