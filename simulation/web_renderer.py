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
        
        # Cache dla tilesetów
        self.tileset_image = None
        self.tileset_cache = {}
        self._load_tileset()
        
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
    
    def _load_tileset(self):
        """Ładuje tileset z mapy TMX."""
        try:
            # Pobierz pierwszy tileset z mapy
            if not hasattr(self.model.map_data, 'tilesets') or len(self.model.map_data.tilesets) == 0:
                print("⚠️  Brak tilesetów w mapie TMX")
                return
            
            tileset = self.model.map_data.tilesets[0]
            print(f"Tileset znaleziony: {tileset}")
            print(f"Tileset atrybuty: {dir(tileset)}")
            
            # Różne sposoby dostępu do ścieżki obrazu w pytmx
            tileset_rel_path = None
            
            # Sposób 1: przez atrybut image
            if hasattr(tileset, 'image'):
                if isinstance(tileset.image, str):
                    tileset_rel_path = tileset.image
                elif hasattr(tileset.image, 'source'):
                    tileset_rel_path = tileset.image.source
            
            # Sposób 2: bezpośrednio przez source
            if not tileset_rel_path and hasattr(tileset, 'source'):
                tileset_rel_path = tileset.source
            
            if not tileset_rel_path:
                print("⚠️  Nie znaleziono źródła obrazu tilesettu w strukturze pytmx")
                print(f"   Dostępne atrybuty: {[a for a in dir(tileset) if not a.startswith('_')]}")
                return
            
            print(f"Ścieżka względna tilesettu: {tileset_rel_path}")
            
            # Buduj pełną ścieżkę
            map_dir = os.path.dirname(os.path.abspath(self.model.map_data.filename))
            tileset_path = os.path.normpath(os.path.join(map_dir, tileset_rel_path))
            
            print(f"Pełna ścieżka do tilesettu: {tileset_path}")
            print(f"Katalog mapy: {map_dir}")
            print(f"Czy plik istnieje: {os.path.exists(tileset_path)}")
            
            if os.path.exists(tileset_path):
                self.tileset_image = Image.open(tileset_path).convert("RGBA")
                print(f"✓ Załadowano tileset: {tileset_path}")
                print(f"  Rozmiar obrazu: {self.tileset_image.size}")
            else:
                print(f"⚠️  BŁĄD: Nie znaleziono obrazu tilesettu!")
                print(f"   Szukano: {tileset_path}")
                
        except Exception as e:
            print(f"❌ Błąd podczas ładowania tilesettu: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_tile_image(self, gid):
        """Pobiera obraz kafelka na podstawie GID."""
        if gid == 0:
            return None  # Pusty kafelek
        
        if gid in self.tileset_cache:
            return self.tileset_cache[gid]
        
        if self.tileset_image is None:
            return None
        
        try:
            # Pobierz informacje o tilesetcie
            tileset = self.model.map_data.tilesets[0]
            tile_id = gid - tileset.firstgid
            
            # Oblicz pozycję kafelka w tileset image
            # Tileset ma spacing=1, więc każdy kafelek to 16px + 1px odstępu
            columns = 32  # Z kafelki_nowe.tsx: columns="32"
            spacing = 1   # Z kafelki_nowe.tsx: spacing="1"
            
            # Pozycja z uwzględnieniem spacing
            col = tile_id % columns
            row = tile_id // columns
            
            tile_x = col * (self.tile_size + spacing)
            tile_y = row * (self.tile_size + spacing)
            
            # Wytnij kafelek (bez spacing)
            tile = self.tileset_image.crop((
                tile_x, tile_y,
                tile_x + self.tile_size, tile_y + self.tile_size
            ))
            
            # Przeskaluj do rozmiaru docelowego (nearest neighbor dla pixel art)
            scaled_tile = tile.resize(
                (self.tile_size * self.scale, self.tile_size * self.scale),
                Image.Resampling.NEAREST
            )
            
            self.tileset_cache[gid] = scaled_tile
            return scaled_tile
        except Exception as e:
            print(f"❌ Błąd przy pobieraniu kafelka GID {gid}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def render_frame(self):
        """Renderuje aktualny stan symulacji jako obraz."""
        # Tło - czarne lub domyślne
        image = Image.new("RGB", (self.width, self.height), (50, 50, 50))
        
        # Renderuj mapę z kafelków lub z kosztów ruchu jako fallback
        try:
            layer = self.model.map_data.get_layer_by_name("Teren")
            if not layer:
                print("⚠️  Nie znaleziono warstwy 'Teren'")
                return image
            
            print(f"🗺️  Renderowanie mapy {self.model.width}x{self.model.height}")
            print(f"   Tileset załadowany: {self.tileset_image is not None}")
            if layer:
                for x in range(self.model.width):
                    for y in range(self.model.height):
                        gid = layer.data[y][x]
                        
                        # Odwrócona oś Y dla prawidłowego wyświetlania
                        img_x = x * self.tile_size * self.scale
                        img_y = (self.model.height - y - 1) * self.tile_size * self.scale
                        
                        if gid != 0 and self.tileset_image is not None:
                            # Renderuj z tilesettu
                            tile_img = self._get_tile_image(gid)
                            if tile_img:
                                image.paste(tile_img, (img_x, img_y), tile_img)
                        else:
                            # Fallback: koloruj według kosztów ruchu
                            cost = self.model.terrain_costs[y, x]
                            if cost < 1.2:
                                color = (100, 200, 100)  # Łatwy teren - jasna zieleń
                            elif cost < 1.5:
                                color = (150, 150, 80)   # Średni teren - żółtobrązowy
                            elif cost < 2.0:
                                color = (120, 100, 70)   # Trudny teren - brąz
                            else:
                                color = (80, 80, 80)     # Bardzo trudny - szary
                            
                            draw_temp = ImageDraw.Draw(image)
                            draw_temp.rectangle(
                                [img_x, img_y, 
                                 img_x + self.tile_size * self.scale - 1, 
                                 img_y + self.tile_size * self.scale - 1],
                                fill=color
                            )
        except Exception as e:
            print(f"Błąd podczas renderowania mapy: {e}")
            import traceback
            traceback.print_exc()
        
        draw = ImageDraw.Draw(image)
        
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
