from PIL import Image, ImageDraw
import os

class WebRenderer:
    """Renderer do generowania obrazów symulacji dla interfejsu webowego."""
    
    def __init__(self, model, tile_size=16, scale=2):
        self.model = model
        # Use map's native tile dimensions when available
        map_data = getattr(model, 'map_data', None)
        if map_data is not None:
            self.tile_width = getattr(map_data, 'tilewidth', tile_size)
            self.tile_height = getattr(map_data, 'tileheight', tile_size)
        else:
            self.tile_width = tile_size
            self.tile_height = tile_size

        self.scale = scale  # Skalowanie dla lepszej widoczności w przeglądarce
        self.width = model.width * self.tile_width * self.scale
        self.height = model.height * self.tile_height * self.scale

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
                new_w = int(self.tile_width * self.scale * 0.8)
                new_h = int(self.tile_height * self.scale * 0.8)
                sprite = sprite.resize((new_w, new_h), Image.Resampling.LANCZOS)
                self.sprite_cache[sprite_path] = sprite
                return sprite
        except Exception as e:
            print(f"Błąd ładowania sprite: {sprite_path}, {e}")
        
        # Fallback - kolorowy kwadrat
        return self._create_fallback_sprite()
    
    def _create_fallback_sprite(self):
        """Tworzy prosty sprite zastępczy."""
        w = int(self.tile_width * self.scale * 0.8)
        h = int(self.tile_height * self.scale * 0.8)
        sprite = Image.new("RGBA", (w, h), (100, 100, 100, 255))
        return sprite
    
    def _load_tileset(self):
        """Ładuje wszystkie tilesety z mapy TMX i cache'uje obrazy oraz metadane."""
        try:
            self.tilesets_info = []
            map_data = getattr(self.model, 'map_data', None)
            if map_data is None:
                print("⚠️  Brak map_data w modelu")
                return

            for tileset in map_data.tilesets:
                tileset_rel_path = None
                if hasattr(tileset, 'image'):
                    if isinstance(tileset.image, str):
                        tileset_rel_path = tileset.image
                    elif hasattr(tileset.image, 'source'):
                        tileset_rel_path = tileset.image.source
                if not tileset_rel_path and hasattr(tileset, 'source'):
                    tileset_rel_path = tileset.source

                tileset_info = {
                    'firstgid': getattr(tileset, 'firstgid', 1),
                    'tilewidth': getattr(tileset, 'tilewidth', getattr(self.model.map_data, 'tilewidth', 16)),
                    'tileheight': getattr(tileset, 'tileheight', getattr(self.model.map_data, 'tileheight', 16)),
                    'spacing': getattr(tileset, 'spacing', 0),
                    'margin': getattr(tileset, 'margin', 0),
                    'columns': getattr(tileset, 'columns', None),
                    'tileset_obj': tileset,
                    'image_path': None,
                    'image': None
                }

                if tileset_rel_path:
                    map_dir = os.path.dirname(os.path.abspath(self.model.map_data.filename))
                    tileset_path = os.path.normpath(os.path.join(map_dir, tileset_rel_path))
                    tileset_info['image_path'] = tileset_path
                    if os.path.exists(tileset_path):
                        try:
                            tileset_info['image'] = Image.open(tileset_path).convert('RGBA')
                            print(f"✓ Załadowano tileset image: {tileset_path}")
                        except Exception as e:
                            print(f"⚠️ Nie można załadować obrazu tilesetu {tileset_path}: {e}")
                    else:
                        print(f"⚠️ Plik tilesetu nie istnieje: {tileset_path}")
                else:
                    print(f"⚠️ Nie znaleziono ścieżki do obrazu tilesetu dla firstgid={tileset_info['firstgid']}")

                self.tilesets_info.append(tileset_info)

            # Sortuj według firstgid rosnąco (ułatwia wyszukiwanie)
            self.tilesets_info.sort(key=lambda t: t['firstgid'])

            if not self.tilesets_info:
                print("⚠️  Brak informacji o tilesetach po załadowaniu mapy")
        except Exception as e:
            print(f"❌ Błąd podczas ładowania tilesetów: {e}")
            import traceback
            traceback.print_exc()

    def _get_tile_image(self, gid):
        """Pobiera obraz kafelka na podstawie GID, wybierając właściwy tileset."""
        if gid == 0:
            return None

        if gid in self.tileset_cache:
            return self.tileset_cache[gid]

        if not hasattr(self, 'tilesets_info') or not self.tilesets_info:
            return None

        # Znajdź tileset, którego zakres obejmuje gid. Wybieramy ten z największym firstgid <= gid
        chosen = None
        for ts in self.tilesets_info:
            if gid >= ts['firstgid']:
                chosen = ts
            else:
                break

        if chosen is None:
            return None

        try:
            local_id = gid - chosen['firstgid']
            ts_tile_w = chosen['tilewidth']
            ts_tile_h = chosen['tileheight']
            spacing = chosen.get('spacing', 0)
            margin = chosen.get('margin', 0)
            columns = chosen.get('columns')
            tileset_img = chosen.get('image')

            if tileset_img is None:
                return None

            img_w, img_h = tileset_img.size
            if not columns or columns == 0:
                columns = max(1, (img_w - 2 * margin + spacing) // (ts_tile_w + spacing))

            col = local_id % columns
            row = local_id // columns

            tile_x = margin + col * (ts_tile_w + spacing)
            tile_y = margin + row * (ts_tile_h + spacing)

            # upewnij się, że coordinates mieszczą się w obrazie
            if tile_x + ts_tile_w > img_w or tile_y + ts_tile_h > img_h:
                # poza zakresem — zwróć None
                return None

            tile = tileset_img.crop((tile_x, tile_y, tile_x + ts_tile_w, tile_y + ts_tile_h))

            # Scale tile to target tile size in pixels (map tile size * scale)
            target_w = int(self.tile_width * self.scale)
            target_h = int(self.tile_height * self.scale)
            scaled_tile = tile.resize((target_w, target_h), Image.Resampling.NEAREST)

            self.tileset_cache[gid] = scaled_tile
            return scaled_tile
        except Exception as e:
            print(f"❌ Błąd przy pobieraniu kafelka GID {gid}: {e}")
            import traceback
            traceback.print_exc()

        # Fallback: spróbuj użyć API pytmx, jeśli dostępne
        try:
            tmx_get = getattr(self.model.map_data, 'get_tile_image_by_gid', None)
            if callable(tmx_get):
                alt = tmx_get(gid)
                if alt is not None:
                    # alt może być PIL Image lub inny obiekt. Spróbuj skonwertować.
                    if isinstance(alt, Image.Image):
                        tile = alt.convert('RGBA')
                    else:
                        # Jeśli alt to powierzchnia pygame lub inne, spróbuj skonwertować przez bytes
                        try:
                            tile = Image.frombytes('RGBA', alt.get_size(), alt.tobytes())
                        except Exception:
                            tile = None

                    if tile is not None:
                        target_w = int(self.tile_width * self.scale)
                        target_h = int(self.tile_height * self.scale)
                        scaled_tile = tile.resize((target_w, target_h), Image.Resampling.NEAREST)
                        self.tileset_cache[gid] = scaled_tile
                        return scaled_tile
        except Exception as e:
            print(f"⚠️ Fallback pytmx get_tile_image_by_gid failed for GID {gid}: {e}")
            import traceback
            traceback.print_exc()

        return None

    def render_frame(self):
        """Renderuje aktualny stan symulacji jako obraz."""
        # Tło - czarne lub domyślne
        image = self.render_map_only()

        draw = ImageDraw.Draw(image)

        # Rysuj jednostki
        for agent in self.model.schedule.agents:
            pos = agent.get_pos_tuple()

            # Pozycja na obrazie (odwrócona oś Y)
            x = int((pos[0] + 0.5) * self.tile_width * self.scale)
            y = int((self.model.height - pos[1] - 0.5) * self.tile_height * self.scale)

            # Wczytaj i narysuj sprite
            sprite = self.load_sprite(agent.model.unit_params[agent.unit_type]["sprite_path"])
            sprite_x = x - sprite.width // 2
            sprite_y = y - sprite.height // 2

            # Narysuj sprite
            image.paste(sprite, (sprite_x, sprite_y), sprite)

            # Rysuj paski HP i morale
            self._draw_health_bars(image, x, y, agent)

        return image

    def render_map_only(self):
        """Renderuje samą mapę (tło) bez jednostek."""
        image = Image.new("RGB", (self.width, self.height), (50, 50, 50))
        
        # Renderuj mapę z kafelków lub z kosztów ruchu jako fallback
        try:
            layer = self.model.map_data.get_layer_by_name("Teren")
            if not layer:
                print("⚠️  Nie znaleziono warstwy 'Teren'")
                return image
            
            for x in range(self.model.width):
                for y in range(self.model.height):
                    raw_gid = layer.data[y][x]
                    gid = raw_gid & 0x1FFFFFFF

                    # First try pytmx helper which handles tileset selection and flip flags
                    tmx_get = getattr(self.model.map_data, 'get_tile_image_by_gid', None)
                    tile_img = None
                    if callable(tmx_get):
                        try:
                            alt = tmx_get(raw_gid)
                            if alt is not None:
                                if isinstance(alt, Image.Image):
                                    tile_img = alt.convert('RGBA')
                                else:
                                    # try to handle pygame Surface or similar
                                    try:
                                        size = alt.get_size()
                                        tile_img = Image.frombytes('RGBA', size, alt.tobytes())
                                    except Exception:
                                        tile_img = None
                                if tile_img is not None:
                                    # scale to target tile size
                                    target_w = int(self.tile_width * self.scale)
                                    target_h = int(self.tile_height * self.scale)
                                    tile_img = tile_img.resize((target_w, target_h), Image.Resampling.NEAREST)
                        except Exception:
                            tile_img = None

                    # Pozycja pikselowa na obrazie
                    img_x = int(x * self.tile_width * self.scale)
                    img_y = int((self.model.height - y - 1) * self.tile_height * self.scale)

                    # If pytmx didn't yield a tile, fallback to manual tileset extraction
                    if gid != 0 and tile_img is None:
                        tile_img = self._get_tile_image(gid)
                        # tile_img may be None if not found

                    if tile_img:
                        image.paste(tile_img, (img_x, img_y), tile_img)
                    else:
                        # no tile image found for this gid -> fallback to terrain color
                        cost = None
                        try:
                            cost = self.model.terrain_costs[y, x]
                        except Exception:
                            cost = None

                        if cost is not None:
                            if cost < 1.2:
                                color = (100, 200, 100)  # Łatwy teren - jasna zieleń
                            elif cost < 1.5:
                                color = (150, 150, 80)   # Średni teren - żółtobrązowy
                            elif cost < 2.0:
                                color = (120, 100, 70)   # Trudny teren - brąz
                            else:
                                color = (80, 80, 80)     # Bardzo trudny - szary
                        else:
                            color = (50, 50, 50)

                        draw_temp = ImageDraw.Draw(image)
                        draw_temp.rectangle([
                            img_x, img_y,
                            img_x + int(self.tile_width * self.scale) - 1,
                            img_y + int(self.tile_height * self.scale) - 1
                        ], fill=color)
        except Exception as e:
            print(f"Błąd podczas renderowania mapy: {e}")
            import traceback
            traceback.print_exc()

        return image

    def render_heatmap(self, heatmap_data):
        """Renderuje mapę z nałożoną heatmapą."""
        image = self.render_map_only()
        # Używamy RGBA do rysowania półprzezroczystych prostokątów
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        width = heatmap_data['width']
        height = heatmap_data['height']
        crown_map = heatmap_data['crown']
        cossack_map = heatmap_data['cossack']

        # Znajdź maksimum do normalizacji
        max_val = 1
        for row in crown_map: max_val = max(max_val, max(row) if row else 0)
        for row in cossack_map: max_val = max(max_val, max(row) if row else 0)

        import math

        for y in range(height):
            for x in range(width):
                c_val = crown_map[y][x]
                k_val = cossack_map[y][x]

                if c_val > 0 or k_val > 0:
                    # Pozycja na obrazie (odwrócona oś Y, tak jak w render_frame)
                    img_x = int(x * self.tile_width * self.scale)
                    img_y = int((self.model.height - y - 1) * self.tile_height * self.scale)

                    # Normalizacja logarytmiczna dla lepszej widoczności
                    c_intensity = min(1.0, math.log(c_val + 1) / math.log(max_val + 1) * 2.5)
                    k_intensity = min(1.0, math.log(k_val + 1) / math.log(max_val + 1) * 2.5)

                    r = int(c_intensity * 255)
                    b = int(k_intensity * 255)
                    g = 0
                    # Alpha zależy od intensywności
                    a = int(min(0.8, max(c_intensity, k_intensity) * 0.8 + 0.2) * 255)

                    # Rysuj prostokąt
                    draw.rectangle(
                        [img_x, img_y,
                         img_x + int(self.tile_width * self.scale),
                         img_y + int(self.tile_height * self.scale)],
                        fill=(r, g, b, a)
                    )

        # Połącz mapę z nakładką
        image = image.convert("RGBA")
        return Image.alpha_composite(image, overlay)

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
