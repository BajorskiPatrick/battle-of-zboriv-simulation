# 📊 ROZBUDOWANE PODSUMOWANIE: Symulacja Bitwy pod Zborowem

## **🎯 Architektura Systemu**

Projekt implementuje **symulację agentową (Agent-Based Model)** bitwy historycznej z wyraźnym podziałem na 3 warstwy:

1. **Warstwa logiki** (`simulation/`) - zarządza modelem i zachowaniem agentów
2. **Warstwa wizualizacji** (`visualization/`) - renderuje symulację w czasie rzeczywistym
3. **Warstwa główna** (`main.py`) - punkt wejścia aplikacji

---

## **🧠 I. MODEL SYMULACJI (`simulation/model.py`)**

### **Klasa `BattleOfZborowModel` - Serce Symulacji**

**Rola:** Centralny manager całej symulacji - tworzy świat, teren, jednostki i zarządza czasem.

**Kluczowe elementy:**

### 1. **Teren z mapy Tiled:**
- Wczytuje mapę z pliku `.tmx` (format Tiled Map Editor)
- Konwertuje właściwości kafelków (`movement_cost`) na macierz kosztów ruchu
- Różne tereny (równina, bagna, wzgórza) mają różne koszty przemieszczania
- Tworzy siatkę (`Grid`) dla algorytmu pathfindingu

### 2. **System typów jednostek (`unit_params`):**

Definiuje **6 rodzajów wojsk** z realistycznymi parametrami:

#### **Armia Koronna:**
- **`Piechota`** - wysoka wytrzymałość (HP: 120), średni zasięg (5), wolna (speed: 1)
- **`Dragonia`** - mobilna piechota, może strzelać i manewrować (speed: 2, range: 6)
- **`Jazda`** - kawaleria szarżująca, potężne obrażenia (damage: 20), szybka (speed: 3)
- **`Pospolite Ruszenie`** - najsłabsza jednostka, niskie morale (40), podatna na panikę

#### **Kozacy/Tatarzy:**
- **`Piechota Kozacka`** - wysoka determinacja (morale: 110), większe obrażenia (12)
- **`Jazda Tatarska`** - najszybsza jednostka (speed: 4), taktyka hit-and-run (range: 7)

### 3. **Rozmieszczenie sił (`setup_agents`):**
- **Armia Koronna**: 5 jednostek piechoty + 3 jednostki jazdy na **dole mapy**
- **Kozacy/Tatarzy**: 5 jednostek piechoty kozackiej + 5 jednostek jazdy tatarskiej na **górze mapy**
- Jednostki losowo rozmieszczone w swoich strefach startowych
- Każda jednostka dostaje **cel strategiczny** po drugiej stronie mapy → armie nieuchronnie się spotkają

### 4. **Mechanizm kroku czasowego:**
- `step()` wywołuje `schedule.step()` → aktywuje wszystkich agentów
- Wykorzystuje `RandomActivation` → kolejność wykonania agentów jest losowa (większy realizm)

---

## **🤖 II. LOGIKA JEDNOSTEK (`simulation/agent.py`)**

### **Klasa `MilitaryAgent` - Inteligentny Żołnierz**

**Fundament:** Implementacja **FSM (Finite State Machine)** - maszyny stanów skończonych.

---

## **🔄 Stany Agenta:**

Agent może być w jednym z 4 stanów:

1. **`IDLE`** - bezczynność (stan początkowy)
2. **`MOVING`** - przemieszczanie się
3. **`ATTACKING`** - prowadzenie walki
4. **`FLEEING`** - ucieczka (gdy morale < 25)

---

## **🧩 GŁÓWNA LOGIKA ZACHOWANIA (`step()` method)**

Wykonywana **co krok symulacji** dla każdego agenta:

### **Faza 1: Sprawdzenie przetrwania**
```
Jeśli HP <= 0 → usuń agenta z symulacji (jednostka zniszczona)
```

### **Faza 2: Test morale**
```python
Jeśli morale < 25:
    → zmień stan na FLEEING
    → oblicz ścieżkę do bezpiecznej krawędzi mapy
    → uciekaj bez walki
```
**Realizm:** Jednostki o złamanym morale wycofują się z bitwy (jak Pospolite Ruszenie w rzeczywistości).

### **Faza 3: Detekcja wroga**
```python
Skanuj obszar w promieniu 15 kafelków
Znajdź najbliższego wroga (inna frakcja)
```

### **Faza 4: Taktyka walki** (gdy wykryto wroga)

**Trzy scenariusze oparte na dystansie:**

#### **A) ZASIĘG STRZAŁU** (dystans 2-`attack_range`):
```python
70% szans → ATTACK (strzelanie)
    - 60% szans trafienia
    - Obrażenia: damage punktów HP
    - Dodatkowo: damage * 1.5 obniżenia morale wroga
30% szans → MOVE (zbliż się)
    - Oblicz ścieżkę A* do wroga
    - Przemieść się o 1 krok
```

#### **B) WALKA WRĘCZ** (dystans ≤ 1):
```python
100% → ATTACK (walka bezpośrednia)
    - 80% szans trafienia (większa niż strzał!)
    - Obrażenia: damage * 1.2 (bonus do walki wręcz)
    - Spadek morale: damage * 2 (drastyczny wpływ)
```

#### **C) WRÓG POZA ZASIĘGIEM** (dystans > `attack_range`):
```python
→ MOVE (ścigaj wroga)
    - Oblicz ścieżkę A* do pozycji wroga
    - Idź w jego kierunku
    - Cache ścieżki (nie przeliczaj co krok)
```

### **Faza 5: Ruch strategiczny** (brak wroga)
```python
→ MOVE do celu strategicznego
    - Każda jednostka ma cel po drugiej stronie mapy
    - Armie zmierzają ku sobie
    - Przelicz ścieżkę jeśli krótsza niż 5 kroków
```

---

## **🗺️ System Pathfindingu**

### **Algorytm A*** (`calculate_path()`):

1. Pobiera aktualną pozycję jednostki
2. Sprawdza czy cel jest osiągalny (walkable)
3. Wykorzystuje `AStarFinder` z biblioteki `pathfinding`
4. Uwzględnia koszty terenu z macierzy `terrain_costs`
5. Zwraca optymalną ścieżkę (lista węzłów)

### **Ruch (`move()`):**
- Pobiera następny węzeł ze ścieżki
- Sprawdza czy cel jest wolny
- Przesuwa agenta na siatkę `MultiGrid`
- Jeśli zablokowane → czyści ścieżkę (wymusi ponowne obliczenie)

---

## **💥 System Obrażeń i Morale**

### **Dwa powiązane systemy:**

#### 1. **HP (Punkty Życia):**
- Bezpośrednie obrażenia od ataków
- Gdy HP ≤ 0 → jednostka ginie (usuwana z symulacji)

#### 2. **Morale (Duch Walki):**
- Spada przy otrzymywanych obrażeniach
- Spadek = obrażenia × 1.5 (strzał) lub × 2 (wręcz)
- Gdy < 25 → jednostka ucieka
- Symuluje psychologiczny aspekt bitwy

### **Przykład kaskadowy efekt:**
```
Piechota Kozacka strzela do Pospolitego Ruszenia
→ 12 damage do HP
→ 18 punktów spadku morale
→ Pospolite Ruszenie (morale: 40) po 3 trafieniach: 40 - 54 = panika!
→ Ucieczka z pola bitwy
```

---

## **🎮 III. WIZUALIZACJA (`visualization/`)**

### **`SimulationWindow` - Okno Arcade**

#### **Główna pętla renderingu:**

#### 1. **Setup:**
- Ładuje mapę Tiled jako tło
- Tworzy sprite dla każdej jednostki z odpowiednią grafiką
- Mapuje ID agenta → sprite (słownik `sprite_map`)

#### 2. **On Draw (60 FPS):**
- Rysuje warstwę terenu z mapy
- Rysuje wszystkie sprite'y jednostek
- Rysuje paski HP/morale nad każdą jednostką

#### 3. **On Update (kontrolowana prędkość):**
- **Timer:** Logika symulacji działa z prędkością `SIMULATION_TICKS_PER_SECOND` (5 kroków/s)
- **Synchronizacja:** 
  - Usuwa sprite'y martwych jednostek
  - Aktualizuje pozycje sprite'ów
  - **Płynna animacja:** interpolacja liniowa pozycji (20% na klatkę)

### **`AgentSprite` - Reprezentacja Jednostki**

#### **Funkcje:**

#### 1. **Konstruktor:**
- Pobiera ścieżkę do grafiki z `unit_params` (każdy typ ma własną grafikę)
- Skaluje sprite (80% rozmiaru)

#### 2. **`draw_health_bar()`:**
- Rysuje 2 paski nad jednostką:
  - **Dolny (HP):** Czerwone tło → zielone wypełnienie
  - **Górny (Morale):** Szare tło → cyjan wypełnienie
- Proporcjonalne do wartości `hp/max_hp` i `morale/max_morale`

---

## **⚙️ IV. PRZEPŁYW SYMULACJI**

```
1. main.py
   ↓
2. Tworzy SimulationWindow (Arcade)
   ↓
3. Setup():
   - Ładuje BattleOfZborowModel
   - Model tworzy siatkę, teren, agentów
   - Tworzy sprite'y dla wszystkich jednostek
   ↓
4. arcade.run() → Główna pętla
   ↓
5. on_update() co 1/60 sekundy:
   - Timer: Co 1/5 sekundy → model.step()
     ↓
     → schedule.step()
       ↓
       → agent1.step()
         → Sprawdź morale
         → Znajdź wroga
         → Walcz/Ruszaj/Uciekaj
       → agent2.step()
         → (j.w.)
       → ... (dla wszystkich agentów)
   - Synchronizuj sprite'y z agentami
   ↓
6. on_draw() co 1/60 sekundy:
   - Rysuj mapę
   - Rysuj jednostki
   - Rysuj paski HP/morale
```

---

## **🎲 ELEMENTY LOSOWOŚCI (Realizm)**

1. **Losowe rozmieszczenie** startowe w strefach
2. **Losowa kolejność** aktywacji agentów (RandomActivation)
3. **Losowe cele** strategiczne (wariacje w ruchu)
4. **Szanse na trafienie**: 60% (strzał), 80% (wręcz)
5. **Szansa na atak vs. zbliżenie**: 70/30 na dystansie

---

## **🏆 KLUCZOWE CECHY LOGIKI**

1. **Emergencja:** Złożone wzorce bitwy wynikają z prostych reguł jednostek
2. **Heterogeniczność:** 6 różnych typów jednostek z unikalnymi rolami
3. **Morale jako gamechanger:** Psychologia ważniejsza niż HP
4. **Terrain-aware:** Jednostki liczą ścieżki z uwzględnieniem terenu
5. **Realistyczne zachowania:** Strzał → ruch → walka wręcz → ucieczka

---

## **📈 DYNAMIKA BITWY**

### **Typowy scenariusz:**

1. **Start:** Armie w odległych rogach mapy
2. **Marsz:** Obie strony idą do celów strategicznych (środek)
3. **Kontakt:** Jazda Tatarska (szybka) dociera pierwsza → ostrzeliwuje Koronnych
4. **Zatarcie:** Piechota obu stron spotyka się → walka wręcz
5. **Szarża:** Jazda Koronna uderza w bok Kozaków → duże obrażenia
6. **Załamanie:** Pospolite Ruszenie (słabe morale) ucieka po stratach
7. **Domino effect:** Spadek liczebności → większa presja → więcej ucieczek
8. **Koniec:** Jedna strona dominuje lub obie się wycofują

---

## **🎯 PODSUMOWANIE**

To zaawansowana symulacja wykorzystująca profesjonalne frameworki do stworzenia dynamicznego, emergentnego modelu bitwy historycznej, gdzie **proste reguły AI tworzą złożone, nieprzewidywalne starcia**!

### **Kluczowe technologie:**
- **Mesa** - framework do modelowania agentowego
- **Arcade** - silnik wizualizacji 2D
- **Pathfinding** - algorytm A* z uwzględnieniem terenu
- **PyTMX** - parsowanie map z Tiled

### **Główne mechaniki:**
- FSM (maszyna stanów) dla zachowania jednostek
- System morale wpływający na waleczność
- Pathfinding z uwzględnieniem kosztów terenu
- Losowość zapewniająca unikalność każdej bitwy
- Realistyczne typy jednostek z historycznymi parametrami
