# 🌐 Interfejs Webowy - Symulacja Bitwy pod Zborowem

## 📋 Spis Treści
1. [Nowe Funkcje](#-nowe-funkcje)
2. [Architektura Webowa](#-architektura-webowa)
3. [Instalacja i Uruchomienie](#-instalacja-i-uruchomienie)
4. [Interfejs Użytkownika](#-interfejs-użytkownika)
5. [API Endpoints](#-api-endpoints)

---

## ✨ Nowe Funkcje

### 🎛️ Konfiguracja Jednostek
- **Przed rozpoczęciem symulacji** użytkownik może wybrać dokładną liczbę jednostek każdego typu
- **6 typów jednostek** dostępnych do wyboru:
  - Armia Koronna: Piechota, Dragonia, Jazda, Pospolite Ruszenie
  - Kozacy/Tatarzy: Piechota Kozacka, Jazda Tatarska
- **Zakres**: 0-20 jednostek każdego typu
- **Interaktywne kontrolki**: przyciski +/- oraz pola tekstowe

### 📊 Legenda z Ikonkami
- **Wizualna prezentacja** wszystkich typów jednostek
- **Ikony jednostek** z plików sprite'ów
- **Szczegółowe parametry** dla każdego typu:
  - HP (punkty życia)
  - Morale (duch walki)
  - Zasięg (dystans ataku)
  - Damage (siła obrażeń)
- **Oznaczenie frakcji** kolorami (czerwony/niebieski)

### 🎮 Symulacja w Przeglądarce
- **Pełna symulacja** wyświetlana w czasie rzeczywistym w oknie przeglądarki
- **Wizualizacja na Canvas HTML5**
- **Paski HP i morale** nad każdą jednostką
- **Statystyki na żywo**: liczba jednostek każdej strony
- **Automatyczna detekcja zwycięstwa**

---

## 🏗️ Architektura Webowa

### Backend (Flask)

**Plik: `app.py`**
- Serwer Flask z REST API
- Zarządzanie instancją symulacji
- Generowanie klatek symulacji
- Thread-safe operacje na modelu

### Frontend (HTML/CSS/JavaScript)

**Plik: `templates/index.html`**
- Responsywny interfejs użytkownika
- Trzy główne panele:
  1. Konfiguracja jednostek
  2. Obszar symulacji
  3. Legenda i statystyki
- Real-time rendering na Canvas
- AJAX calls do API

### Renderer

**Plik: `simulation/web_renderer.py`**
- Generowanie obrazów symulacji (PIL/Pillow)
- Rysowanie jednostek, pasków HP/morale
- Cache sprite'ów dla wydajności
- Eksport do base64 lub stream

### Model (Rozszerzony)

**Plik: `simulation/model.py`** - Zmodyfikowany
- Konstruktor przyjmuje `units_config` (słownik z liczbami jednostek)
- Metoda `setup_agents()` tworzy jednostki na podstawie konfiguracji
- Fallback do domyślnego scenariusza gdy brak konfiguracji

---

## 🚀 Instalacja i Uruchomienie

### 1. Zainstaluj zależności

```bash
pip install -r requirements.txt
```

Nowe pakiety:
- `flask` - framework webowy
- `flask-cors` - obsługa CORS
- `pillow` - generowanie obrazów

### 2. Uruchom serwer

```bash
python app.py
```

Output:
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

### 3. Otwórz przeglądarkę

Przejdź do: **http://localhost:5000**

---

## 🎨 Interfejs Użytkownika

### Layout

```
┌─────────────────────────────────────────────────────────┐
│              🏰 BITWA POD ZBOROWEM 1649 ⚔️              │
├──────────────┬────────────────────────┬─────────────────┤
│              │                        │                 │
│ KONFIGURACJA │    SYMULACJA          │    LEGENDA      │
│ JEDNOSTEK    │    (Canvas)            │    & STATS      │
│              │                        │                 │
│ [Armia       │  [Pole bitwy]          │ [Ikony +        │
│  Koronna]    │  • Czerwone = Koronna  │  Parametry]     │
│              │  • Niebieskie = Kozacy │                 │
│ [Kozacy/     │                        │ [Statystyki     │
│  Tatarzy]    │  [Paski HP/Morale]     │  na żywo]       │
│              │                        │                 │
│ [START]      │                        │                 │
│ [STOP]       │                        │                 │
└──────────────┴────────────────────────┴─────────────────┘
```

### Panel Konfiguracji (Lewy)

**Sekcja Armia Koronna** (czerwona):
```
🛡️ Armia Koronna
┌────────────────────────────────┐
│ [icon] Piechota      [-] 0 [+] │
│ [icon] Dragonia      [-] 0 [+] │
│ [icon] Jazda         [-] 0 [+] │
│ [icon] Pospolite R.  [-] 0 [+] │
└────────────────────────────────┘
```

**Sekcja Kozacy/Tatarzy** (niebieska):
```
🏹 Kozacy i Tatarzy
┌────────────────────────────────┐
│ [icon] Piechota Koz. [-] 0 [+] │
│ [icon] Jazda Tatar.  [-] 0 [+] │
└────────────────────────────────┘
```

**Przyciski kontrolne**:
- 🚀 **Rozpocznij Symulację** - zielony gradient
- ⏹️ **Zatrzymaj Symulację** - różowy gradient

### Panel Symulacji (Środek)

- **Status symulacji** (lewy górny róg):
  - ⏸️ Gotowa do startu (szary)
  - ▶️ Symulacja w toku (zielony)
  - ⏹️ Symulacja zatrzymana (czerwony)

- **Canvas**: 
  - Zielone tło (pole bitwy)
  - Strefy startowe (półprzezroczyste)
  - Jednostki jako kolorowe kropki
  - Paski HP (zielony) i morale (cyan) nad jednostkami

### Panel Legendy (Prawy)

**Legenda jednostek**:
```
┌──────────────────────────────────┐
│ [icon] Piechota                  │
│        Armia Koronna              │
│        HP: 120  |  Morale: 100    │
│        Zasięg: 5  |  Atak: 10     │
├──────────────────────────────────┤
│ [icon] Piechota Kozacka          │
│        Kozacy/Tatarzy             │
│        HP: 100  |  Morale: 110    │
│        Zasięg: 5  |  Atak: 12     │
└──────────────────────────────────┘
```

**Statystyki bitwy** (pojawia się po starcie):
```
📊 Statystyki Bitwy
─────────────────────
Armia Koronna:      8
Kozacy/Tatarzy:    10
Łącznie jednostek: 18
```

---

## 🔌 API Endpoints

### `GET /`
**Główna strona**
- Zwraca: `index.html`

### `GET /api/unit-types`
**Pobierz dostępne typy jednostek**

Response:
```json
{
  "Piechota": {
    "faction": "Armia Koronna",
    "hp": 120,
    "morale": 100,
    "range": 5,
    "damage": 10,
    "speed": 1,
    "description": "Wysoka dyscyplina...",
    "sprite_path": "assets/sprites/crown_infantry.png"
  },
  ...
}
```

### `POST /api/start-simulation`
**Rozpocznij nową symulację**

Request body:
```json
{
  "Piechota": 5,
  "Jazda": 3,
  "Piechota Kozacka": 5,
  "Jazda Tatarska": 5
}
```

Response:
```json
{
  "status": "started",
  "message": "Symulacja rozpoczęta"
}
```

### `POST /api/stop-simulation`
**Zatrzymaj symulację**

Response:
```json
{
  "status": "stopped",
  "message": "Symulacja zatrzymana"
}
```

### `GET /api/simulation-step`
**Pobierz aktualny stan symulacji**

Response:
```json
{
  "agents": [
    {
      "id": 1,
      "faction": "Armia Koronna",
      "unit_type": "Piechota",
      "x": 45,
      "y": 78,
      "hp": 120,
      "max_hp": 120,
      "morale": 100,
      "max_morale": 100,
      "state": "MOVING",
      "sprite_path": "assets/sprites/crown_infantry.png"
    },
    ...
  ],
  "stats": {
    "crown_count": 8,
    "cossack_count": 10,
    "total_agents": 18
  },
  "running": true,
  "map_width": 100,
  "map_height": 80
}
```

### `GET /api/simulation-frame`
**Pobierz obraz symulacji (alternatywna wizualizacja)**

Response:
```json
{
  "frame": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "running": true
}
```

### `GET /api/video-feed`
**Stream MJPEG (opcjonalny)**
- Continuous stream klatek jako multipart JPEG
- Można użyć jako `<img src="/api/video-feed">`

---

## 🎯 Przykłady Użycia

### Scenariusz 1: Szybki Test
```javascript
// Konfiguracja
Piechota: 3
Piechota Kozacka: 3

// Start
Click "Rozpocznij Symulację"

// Obserwuj
- Jednostki zbliżają się do siebie
- Rozpoczyna się wymiana ognia
- Morale spada przy obrażeniach
```

### Scenariusz 2: Dominacja Kawalerii
```javascript
// Konfiguracja
Jazda: 10
Jazda Tatarska: 10

// Oczekiwany rezultat
- Bardzo szybkie starcie
- Duże obrażenia w walce wręcz
- Szybkie załamanie morale
```

### Scenariusz 3: Testowanie Morale
```javascript
// Konfiguracja
Pospolite Ruszenie: 15  (morale: 40)
Piechota Kozacka: 5     (morale: 110)

// Obserwuj
- Pospolite Ruszenie szybko traci morale
- Ucieczki po kilku trafieniach
- Kozacy wygrywają przez wyższą determinację
```

---

## 🛠️ Techniczne Detale

### Threading
- Flask działa w trybie `threaded=True`
- Symulacja chroniona przez `threading.Lock()`
- Bezpieczne współbieżne wywołania API

### Wydajność
- Rendering: 5 FPS (krok symulacji co 200ms)
- Canvas update: 60 FPS (przeglądarka)
- Sprite cache w `WebRenderer`

### Compatibility
- Przeglądarki: Chrome, Firefox, Edge, Safari
- HTML5 Canvas required
- JavaScript ES6+

---

## 🔧 Rozszerzenia (Przyszłość)

Możliwe ulepszenia:
1. **WebSocket** zamiast polling dla lepszej wydajności
2. **Replay systemu** - zapis i odtwarzanie bitew
3. **Eksport do wideo** - generowanie MP4
4. **Multiplayer** - dwóch graczy konfiguruje swoje armie
5. **AI przeciwnik** - komputer dobiera jednostki
6. **Mapa terenu** - wizualizacja kosztów ruchu
7. **Szczegółowe statystyki** - wykresy, heatmapy

---

## 📝 Notatki dla Developera

### Struktura plików (nowe/zmienione):
```
battle-of-zboriv-simulation/
├── app.py                    # NEW - Flask server
├── templates/
│   └── index.html           # NEW - Web UI
├── simulation/
│   ├── model.py             # MODIFIED - units_config param
│   └── web_renderer.py      # NEW - PIL renderer
├── visualization/
│   └── window.py            # MODIFIED - None param
├── requirements.txt         # MODIFIED - +flask, pillow
└── WEB_INTERFACE.md        # NEW - dokumentacja
```

### Testowanie:
```bash
# Test API
curl http://localhost:5000/api/unit-types

# Test startu
curl -X POST http://localhost:5000/api/start-simulation \
  -H "Content-Type: application/json" \
  -d '{"Piechota": 5, "Piechota Kozacka": 5}'

# Test stanu
curl http://localhost:5000/api/simulation-step
```

---

Miłej zabawy z nowym interfejsem webowym! 🎉
