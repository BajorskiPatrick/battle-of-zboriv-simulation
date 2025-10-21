# 🐛 Debug Guide - Rozwiązywanie problemów

## Problem: Jednostki się nie poruszają

### Krok 1: Sprawdź konsolę przeglądarki
1. Otwórz przeglądarkę (Chrome/Firefox/Edge)
2. Naciśnij **F12**
3. Przejdź do zakładki **Console**
4. Uruchom symulację
5. Szukaj komunikatów:
   - `"Starting simulation with config:"` - konfiguracja wysłana
   - `"Start response: 200"` - backend odpowiedział OK
   - `"Simulation interval started"` - polling uruchomiony
   - `"Simulation step:"` - dane z każdego kroku

### Krok 2: Sprawdź terminal serwera
W terminalu gdzie uruchomiłeś `python app.py` szukaj:
```
Otrzymana konfiguracja: {'Piechota': 2, 'Piechota Kozacka': 2}
Executing step... Agents: 4
Agent 1 at (45, 78) has no path to (50, 40)
```

### Krok 3: Sprawdź sieć (Network tab)
1. F12 → zakładka **Network**
2. Filtruj: **Fetch/XHR**
3. Szukaj zapytań:
   - `POST /api/start-simulation` - status 200?
   - `GET /api/simulation-step` - powtarza się co 200ms?
4. Kliknij na zapytanie i zobacz **Response**

---

## Najczęstsze problemy i rozwiązania

### Problem: "Symulacja nie została rozpoczęta"

**Przyczyna:** Backend nie otrzymał konfiguracji

**Rozwiązanie:**
1. Sprawdź czy Flask działa: `http://localhost:5000/api/unit-types`
2. Sprawdź console przeglądarki dla błędów CORS
3. Uruchom ponownie `python app.py`

### Problem: Jednostki stoją w miejscu

**Możliwe przyczyny:**

#### A) Pathfinding nie działa
**Objawy w konsoli serwera:**
```
Agent 1 at (45, 78) has no path to (50, 40)
```

**Rozwiązanie:**
- Mapa może nie być załadowana poprawnie
- Sprawdź czy plik `assets/map/zborow_battlefield.tmx` istnieje
- Terrain layer może być niepoprawny

**Fix:**
```python
# W simulation/model.py sprawdź load_terrain_data()
# Powinno pokazać: "Używam domyślnych kosztów ruchu"
```

#### B) Step() nie jest wywoływany
**Objawy w konsoli serwera:**
Brak linii: `"Executing step... Agents: X"`

**Rozwiązanie:**
- `simulation_running` może być False
- Sprawdź czy interval w JS został uruchomiony

#### C) Cele strategiczne poza mapą
**Objawy:**
Jednostki mają cele (x, y) poza zakresem mapy

**Rozwiązanie:**
Kod już naprawiony - cele są teraz walidowane

---

## Test manualny w konsoli Python

```python
# Zatrzymaj Flask (Ctrl+C)
# Uruchom Python w terminalu:
python

# Testuj model bezpośrednio:
from simulation.model import BattleOfZborowModel

config = {
    "Piechota": 2,
    "Piechota Kozacka": 2
}

model = BattleOfZborowModel("assets/map/zborow_battlefield.tmx", config)

print(f"Agenci: {len(model.schedule.agents)}")
print(f"Wymiary mapy: {model.width} x {model.height}")

# Test jednego kroku
for agent in model.schedule.agents:
    print(f"Agent {agent.unique_id}: pos={agent.get_pos_tuple()}, target={agent.strategic_target}")

model.step()

for agent in model.schedule.agents:
    print(f"Po kroku: Agent {agent.unique_id}: pos={agent.get_pos_tuple()}, state={agent.state}")
```

**Oczekiwany output:**
```
Agenci: 4
Wymiary mapy: 100 x 80
Agent 1: pos=(45, 78), target=(50, 40)
Agent 2: pos=(42, 75), target=(55, 35)
...
Po kroku: Agent 1: pos=(45, 77), state=MOVING
Po kroku: Agent 2: pos=(42, 74), state=MOVING
```

Jeśli pozycje się NIE ZMIENIAJĄ = problem z pathfindingiem!

---

## Test pathfindingu

```python
from simulation.model import BattleOfZborowModel

model = BattleOfZborowModel("assets/map/zborow_battlefield.tmx", {"Piechota": 1})
agent = list(model.schedule.agents)[0]

print(f"Agent na pozycji: {agent.get_pos_tuple()}")
print(f"Cel strategiczny: {agent.strategic_target}")

# Spróbuj obliczyć ścieżkę
agent.calculate_path(agent.strategic_target)

print(f"Długość ścieżki: {len(agent.path)}")

if len(agent.path) > 0:
    print("✅ Pathfinding działa!")
    print(f"Pierwsze 5 kroków: {agent.path[:5]}")
else:
    print("❌ Pathfinding NIE działa!")
    print("Sprawdź terrain_costs i Grid")
```

---

## Szybkie testy w przeglądarce

### Test 1: API działa?
Otwórz w przeglądarce:
```
http://localhost:5000/api/unit-types
```

Powinien pokazać JSON z jednostkami.

### Test 2: Start ręczny
W konsoli przeglądarki (F12):
```javascript
// Start symulacji
fetch('/api/start-simulation', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({'Piechota': 2, 'Piechota Kozacka': 2})
}).then(r => r.json()).then(console.log);

// Sprawdź krok
fetch('/api/simulation-step')
    .then(r => r.json())
    .then(data => console.log(data.stats));
```

### Test 3: Polling działa?
```javascript
// Uruchom ręczny interval
let count = 0;
let testInterval = setInterval(async () => {
    const response = await fetch('/api/simulation-step');
    const data = await response.json();
    console.log(`Step ${count++}:`, data.stats);
    
    if (count > 10) clearInterval(testInterval);
}, 200);
```

---

## Checklist naprawy

- [ ] Flask uruchomiony (`python app.py`)
- [ ] Port 5000 dostępny (sprawdź `localhost:5000`)
- [ ] Przeglądarka otwarta na `localhost:5000`
- [ ] Console przeglądarki (F12) bez błędów
- [ ] Dodano jednostki (minimum 1 z każdej strony)
- [ ] Kliknięto "Rozpocznij Symulację"
- [ ] Status zmienił się na "Symulacja w toku"
- [ ] Console pokazuje `"Simulation step:"` co 200ms
- [ ] Terminal serwera pokazuje `"Executing step..."`
- [ ] Pozycje jednostek się zmieniają w danych JSON

---

## Logi debug

### Włączone logi:
1. **Python (app.py):**
   - `print(f"Otrzymana konfiguracja: {config}")`
   - `print(f"Executing step... Agents: {len(simulation.schedule.agents)}")`

2. **Python (agent.py):**
   - Fleeing: `print(f"Agent {self.unique_id} ({self.unit_type}) FLEEING!")`
   - No path: `print(f"Agent {self.unique_id} at {current_pos} has no path...")`

3. **JavaScript (index.html):**
   - `console.log('Starting simulation with config:', config);`
   - `console.log('Simulation step:', data.stats);`

### Wyłącz debug logi:
Zakomentuj lub usuń wszystkie `print()` i `console.log()` po naprawie.

---

## Restart kompletny

Jeśli nic nie działa:

```bash
# 1. Zatrzymaj Flask (Ctrl+C)
# 2. Wyczyść cache Python
cd battle-of-zboriv-simulation
rm -rf simulation/__pycache__
rm -rf visualization/__pycache__

# 3. Reinstaluj zależności
pip install --upgrade -r requirements.txt

# 4. Uruchom ponownie
python app.py

# 5. Otwórz nową kartę przeglądarki (Ctrl+Shift+N - tryb incognito)
# 6. Przejdź do localhost:5000
```

---

Powodzenia! 🐛🔧
