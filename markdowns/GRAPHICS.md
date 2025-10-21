# 🎨 Grafika i Assety - Instrukcja

## 📁 Struktura Plików Graficznych

```
assets/
├── sprites/           # Ikony jednostek (32x32 px)
│   ├── crown_infantry.png      # Piechota Koronna
│   ├── crown_dragoon.png       # Dragonia Koronna
│   ├── crown_cavalry.png       # Jazda Koronna
│   ├── crown_levy.png          # Pospolite Ruszenie
│   ├── cossack_infantry.png    # Piechota Kozacka
│   └── cossack_cavalry.png     # Jazda Tatarska
└── map/
    ├── zborow_battlefield.tmx  # Mapa Tiled
    └── tileset.tsx             # Zestaw kafelków
```

---

## 🖼️ Sprite'y Jednostek

### Format:
- **Rozmiar:** 32x32 piksele (lub większe, auto-skalowane)
- **Format:** PNG z przezroczystością (alpha channel)
- **Kolory:** Pełna paleta RGB

### Nazewnictwo:
```
{faction}_{unit_type}.png

Przykłady:
- crown_infantry.png    (Armia Koronna - Piechota)
- cossack_cavalry.png   (Kozacy - Jazda)
```

---

## 🎨 Fallback Shapes (gdy brak sprite'a)

Jeśli sprite nie może zostać załadowany, system automatycznie rysuje kształty:

| Typ Jednostki | Kształt | Kolor Koronna | Kolor Kozacy |
|--------------|---------|---------------|--------------|
| Piechota / Infantry | ⬜ Kwadrat | 🔴 Czerwony | 🔵 Niebieski |
| Jazda / Cavalry | 🔺 Trójkąt | 🔴 Czerwony | 🔵 Niebieski |
| Dragonia | 🔶 Romb | 🔴 Czerwony | 🔵 Niebieski |
| Inne | ⚫ Koło | 🔴 Czerwony | 🔵 Niebieski |

---

## 🔧 Testowanie Sprite'ów

### Test 1: Sprawdź czy pliki istnieją
```powershell
# PowerShell
ls assets\sprites\*.png
```

**Oczekiwany output:**
```
crown_cavalry.png
crown_dragoon.png
crown_infantry.png
crown_levy.png
cossack_cavalry.png
cossack_infantry.png
```

### Test 2: Sprawdź czy Flask serwuje pliki
Otwórz w przeglądarce:
```
http://localhost:5000/assets/sprites/crown_infantry.png
```

Powinieneś zobaczyć obrazek!

### Test 3: Sprawdź Console
1. F12 → Console
2. Uruchom aplikację
3. Szukaj:
```
Sprites preloaded: 6
```

---

## 🎨 Tworzenie Własnych Sprite'ów

### Wytyczne:
1. **Rozmiar bazowy:** 32x32 px (lub wielokrotność)
2. **Tło:** Przezroczyste (alpha)
3. **Styl:** Pikselowy lub wektorowy
4. **Format:** PNG-24 z alpha channel

### Przykład GIMP/Photoshop:
1. Nowy obraz: 32x32 px, RGB + Alpha
2. Narysuj jednostkę (widok z góry)
3. Eksportuj jako PNG
4. Zapisz w `assets/sprites/`
5. Nazwij zgodnie z konwencją

### Szybkie generowanie (pixel art):
- https://www.piskelapp.com/ (online editor)
- Aseprite (desktop app)
- LibreSprite (darmowy)

---

## 🗺️ Mapa Terenu

### Format: Tiled Map (.tmx)
Utworzone w **Tiled Map Editor**: https://www.mapeditor.org/

### Struktura:
```
zborow_battlefield.tmx
├── Layer: "Teren"        # Warstwa z kafelkami terenu
│   └── Properties:
│       └── movement_cost # Koszt przemieszczenia (float)
└── Tileset: tileset.tsx  # Zbiór grafik kafelków
```

### Movement Cost:
- `1.0` - Równina (normalny ruch)
- `1.5` - Lekkie przeszkody
- `2.0` - Trudny teren (bagno, wzgórza)
- `999` - Nieprzekraczalny teren (woda, skały)

---

## 🔄 Cache Sprite'ów

### JavaScript Cache:
```javascript
spriteCache = {
    "assets/sprites/crown_infantry.png": Image { ... },
    "assets/sprites/cossack_cavalry.png": Image { ... },
    ...
}
```

### Preloading:
Wszystkie sprite'y są ładowane przy starcie aplikacji aby zapewnić płynność.

### Clear cache:
```javascript
// W konsoli przeglądarki
spriteCache = {};
preloadSprites(); // Reload wszystkich
```

---

## 🐛 Troubleshooting

### Problem: Sprite'y nie ładują się

**Sprawdź:**
1. ✅ Pliki istnieją w `assets/sprites/`
2. ✅ Flask uruchomiony (`python app.py`)
3. ✅ Endpoint działa: `http://localhost:5000/assets/sprites/crown_infantry.png`
4. ✅ Console (F12) pokazuje: `"Sprites preloaded: 6"`

**Fix:**
```bash
# Upewnij się że pliki są w odpowiednim miejscu
ls assets/sprites/

# Restart Flask
# Ctrl+C, potem:
python app.py

# Hard refresh przeglądarki
# Ctrl+Shift+R (lub Ctrl+F5)
```

### Problem: "Failed to load sprite"

**Console pokazuje:**
```
Failed to load sprite: assets/sprites/crown_infantry.png
```

**Przyczyna:** Plik nie istnieje lub ścieżka jest błędna

**Fix:**
1. Sprawdź czy plik istnieje
2. Sprawdź nazwę (case-sensitive!)
3. Sprawdź czy Flask routing działa

### Problem: Sprite'y są rozmazane

**Przyczyna:** Automatyczne skalowanie przez Canvas

**Fix już zaimplementowany:**
```javascript
// Canvas używa LANCZOS resampling dla smooth scaling
sprite.resize((new_size, new_size), Image.Resampling.LANCZOS)
```

### Problem: Widzę kształty zamiast sprite'ów

**To normalne!** Fallback shapes są pokazywane gdy:
- Sprite nie może być załadowany
- Network error
- Błędna ścieżka

**Sprawdź Console (F12) dla błędów ładowania.**

---

## 📊 Wizualizacja Mapy

### Aktualnie:
- ✅ **Renderowanie rzeczywistej mapy z Tiled**
- ✅ Każdy tile z `zborow_battlefield.tmx` jest rysowany na Canvas
- ✅ Automatyczne ładowanie tileset.png
- ✅ Wsparcie dla różnych typów terenu (równiny, rzeki, bagno)
- ✅ Strefy startowe (obramowania czerwone/niebieskie)
- ✅ Sprite'y jednostek nakładane na mapę
- ✅ Paski HP/Morale

### Jak działa:
1. **Backend** (`/api/map-data`): Parsuje plik TMX, zwraca siatkę tile IDs
2. **Frontend**: Pobiera `tileset.png` i dane mapy
3. **Canvas**: Dla każdego tile wycina odpowiedni fragment z tilesettu
4. **Renderowanie**: 
   - Tile ID 0 = pusty (przezroczysty)
   - Tile ID 1 = równina (zielony)
   - Tile ID 49 = rzeka/bagno (niebieski/brązowy)

### Szczegóły techniczne:
```javascript
// Tileset: 12 kolumn x 11 rzędów (132 tiles)
// Tile size: 16x16 px (skalowane 2x na Canvas = 32x32 px)
// Mapa: 80x50 tiles = 1280x800 px (2560x1600 px po skalowaniu)

for (let y = 0; y < mapData.height; y++) {
    for (let x = 0; x < mapData.width; x++) {
        const gid = mapData.tiles[y][x];
        const tileId = gid - 1; // firstgid=1
        
        // Oblicz pozycję w tilesetcie
        const srcX = (tileId % 12) * 16;
        const srcY = Math.floor(tileId / 12) * 16;
        
        // Rysuj na Canvas
        ctx.drawImage(tileset, srcX, srcY, 16, 16, destX, destY, 32, 32);
    }
}
```

### Opcjonalnie (przyszłość):
- [ ] Wizualizacja kosztów ruchu (overlay)
- [ ] Efekty terenu (animacje)
- [ ] Mini-mapa

---

## 🎨 Paleta Kolorów

### Jednostki:
- **Armia Koronna:** `#ff6b6b` (czerwony)
- **Kozacy/Tatarzy:** `#4dabf7` (niebieski)

### UI:
- **HP pełny:** `#0c0` (zielony)
- **HP pusty:** `#c00` (czerwony)
- **Morale pełny:** `#0cc` (cyan)
- **Morale pusty:** `#666` (szary)

### Mapa:
- **Tło:** `#2d5016` (ciemny zielony - pole)
- **Siatka:** `rgba(0, 0, 0, 0.1)` (czarny 10%)
- **Strefa Koronna:** `rgba(200, 50, 50, 0.1)` (czerwony 10%)
- **Strefa Kozacy:** `rgba(50, 50, 200, 0.1)` (niebieski 10%)

---

Miłej zabawy z grafiką! 🎨✨
