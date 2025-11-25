# Raport z Przebiegu Pracy: Symulacja Bitwy pod Zborowem (1649)

## 1. Wprowadzenie

### 1.1. Cel Projektu

Projekt realizuje **agentową symulację historycznej Bitwy pod Zborowem**, która odbyła się w dniach 15-16 sierpnia 1649 roku. Symulacja została zbudowana w paradygmacie systemów dyskretnych, wykorzystując dane ze źródeł historycznych (m.in. prace W. Kucharskiego i A. Mandzy'ego) do modelowania dynamiki starcia.

### 1.2. Główne Założenia

- **Modelowanie agentowe (ABM)** - każda jednostka wojskowa jest autonomicznym agentem z własną logiką decyzyjną
- **Realistyczne parametry** - jednostki posiadają atrybuty oparte na danych historycznych
- **Dynamiczna symulacja** - bitwa rozwija się emergentnie na podstawie prostych reguł
- **Wizualizacja w czasie rzeczywistym** - możliwość obserwacji przebiegu bitwy
- **Interaktywność** - konfiguracja jednostek przed rozpoczęciem symulacji

### 1.3. Zakres Funkcjonalności

Projekt obejmuje:
- ✅ Model symulacji agentowej z 6 typami jednostek
- ✅ System pathfindingu z uwzględnieniem terenu
- ✅ Mechanikę walki, morale i obrażeń
- ✅ Wizualizację desktopową (Arcade)
- ✅ Interfejs webowy (Flask + HTML5 Canvas)
- ✅ Konfigurację jednostek przed bitwą
- ✅ Statystyki na żywo
- ✅ Mapę terenu z różnymi typami terenu

---

## 2. Zastosowane Technologie

### 2.1. Backend i Symulacja

| Technologia | Wersja | Zastosowanie |
|------------|--------|--------------|
| **Python** | 3.9+ | Język programowania |
| **Mesa** | 2.3.2 | Framework do modelowania agentowego (ABM) |
| **NumPy** | latest | Operacje na macierzach kosztów terenu |
| **Pathfinding** | latest | Algorytm A* do znajdowania ścieżek |
| **PyTMX** | latest | Parsowanie map z Tiled Map Editor |
| **Flask** | latest | Framework webowy (REST API) |
| **Flask-CORS** | latest | Obsługa CORS dla frontendu |
| **Pillow (PIL)** | latest | Generowanie obrazów dla interfejsu webowego |

### 2.2. Wizualizacja

| Technologia | Zastosowanie |
|-------------|--------------|
| **Arcade** | Silnik wizualizacji 2D dla trybu desktop |
| **HTML5 Canvas** | Renderowanie w przeglądarce |
| **CSS3** | Stylizacja interfejsu webowego |
| **JavaScript (ES6+)** | Logika frontendu |

### 2.3. Narzędzia Zewnętrzne

- **Tiled Map Editor** - edytor do tworzenia map kafelkowych
- **Git** - kontrola wersji

---

## 3. Architektura Systemu

### 3.1. Struktura Projektu

```
battle-of-zboriv-simulation/
├── app.py                    # Serwer Flask z REST API
├── main.py                   # Punkt startowy trybu desktop
├── requirements.txt          # Zależności projektu
│
├── simulation/               # Warstwa logiki symulacji
│   ├── model.py             # Główny model (BattleOfZborowModel)
│   ├── agent.py             # Klasa agenta (MilitaryAgent)
│   └── web_renderer.py      # Renderer dla interfejsu webowego
│
├── visualization/            # Warstwa wizualizacji
│   ├── window.py            # Okno Arcade (tryb desktop)
│   └── sprites.py           # Klasy sprite'ów z paskami HP/morale
│
├── templates/                # Szablony HTML
│   └── index.html           # Interfejs webowy
│
├── assets/                   # Zasoby graficzne
│   ├── map/
│   │   ├── zborow_battlefield.tmx  # Mapa Tiled
│   │   └── tileset.png             # Zestaw kafelków
│   └── sprites/             # Grafiki jednostek (32x32 px)
│       ├── crown_infantry.png
│       ├── crown_dragoon.png
│       ├── crown_cavalry.png
│       ├── crown_levy.png
│       ├── cossack_infantry.png
│       └── cossack_cavalry.png
│
└── markdowns/                # Dokumentacja techniczna
    ├── CHANGES.md
    ├── WEB_INTERFACE.md
    ├── SCENARIOS.md
    ├── GRAPHICS.md
    └── DEBUG.md
```

### 3.2. Warstwy Systemu

Projekt został zaprojektowany z wyraźnym podziałem na warstwy:

1. **Warstwa Modelu** (`simulation/`)
   - Zarządzanie symulacją
   - Logika agentów
   - System walki i morale

2. **Warstwa Wizualizacji** (`visualization/`, `templates/`)
   - Renderowanie w trybie desktop (Arcade)
   - Renderowanie w trybie web (Canvas + PIL)

3. **Warstwa Interfejsu** (`app.py`, `templates/index.html`)
   - REST API (Flask)
   - Frontend (HTML/CSS/JS)

---

## 4. Szczegółowy Opis Implementacji

### 4.1. Model Symulacji (`simulation/model.py`)

#### Klasa `BattleOfZborowModel`

**Odpowiedzialność:** Centralny manager całej symulacji - tworzy świat, teren, jednostki i zarządza czasem.

**Kluczowe komponenty:**

1. **Wczytanie mapy terenu**
   - Parsowanie pliku `.tmx` z Tiled Map Editor
   - Konwersja właściwości kafelków na macierz kosztów ruchu
   - Tworzenie siatki dla algorytmu pathfindingu

2. **Definicja typów jednostek (`unit_params`)**
   
   **Armia Koronna:**
   - **Piechota**: HP=120, Morale=100, Zasięg=5, Obrażenia=10, Prędkość=1
   - **Dragonia**: HP=90, Morale=85, Zasięg=6, Obrażenia=8, Prędkość=2
   - **Jazda**: HP=100, Morale=90, Zasięg=1, Obrażenia=20, Prędkość=3
   - **Pospolite Ruszenie**: HP=70, Morale=40, Zasięg=2, Obrażenia=7, Prędkość=2
   
   **Kozacy/Tatarzy:**
   - **Piechota Kozacka**: HP=100, Morale=110, Zasięg=5, Obrażenia=12, Prędkość=1
   - **Jazda Tatarska**: HP=80, Morale=80, Zasięg=7, Obrażenia=9, Prędkość=4

3. **Rozmieszczenie jednostek**
   - Armia Koronna: dolna część mapy
   - Kozacy/Tatarzy: górna część mapy
   - Każda jednostka otrzymuje losowy cel strategiczny w centrum mapy

4. **Mechanizm kroku czasowego**
   - `step()` wywołuje `schedule.step()` → aktywuje wszystkich agentów
   - Wykorzystuje `RandomActivation` → losowa kolejność wykonania

### 4.2. Logika Agentów (`simulation/agent.py`)

#### Klasa `MilitaryAgent`

**Fundament:** Implementacja **FSM (Finite State Machine)** - maszyny stanów skończonych.

**Stany agenta:**
1. **`IDLE`** - bezczynność (stan początkowy)
2. **`MOVING`** - przemieszczanie się
3. **`ATTACKING`** - prowadzenie walki
4. **`FLEEING`** - ucieczka (gdy morale < 25)

**Główna logika (`step()` method):**

```
1. Sprawdzenie przetrwania
   └─ Jeśli HP <= 0 → usuń agenta

2. Test morale
   └─ Jeśli morale < 25 → FLEEING → uciekaj do krawędzi mapy

3. Detekcja wroga
   └─ Skanuj obszar w promieniu 20 kafelków
   └─ Znajdź najbliższego wroga

4. Taktyka walki (gdy wykryto wroga)
   ├─ Zasięg strzału (2-range): 70% atak, 30% ruch
   ├─ Walka wręcz (≤1): 100% atak (80% szans trafienia)
   └─ Poza zasięgiem: ścigaj wroga (ruch)

5. Ruch strategiczny (brak wroga)
   └─ Idź do celu strategicznego
```

**System pathfindingu:**
- Algorytm A* z uwzględnieniem kosztów terenu
- Cache ścieżek (nie przeliczaj co krok)
- Obsługa zablokowanych ścieżek

**System obrażeń i morale:**
- **HP**: Bezpośrednie obrażenia od ataków
- **Morale**: Spada przy otrzymywanych obrażeniach
  - Strzał: spadek morale = obrażenia × 1.5
  - Walka wręcz: spadek morale = obrażenia × 2
- Gdy morale < 25 → jednostka ucieka

### 4.3. Wizualizacja Desktop (`visualization/window.py`)

#### Klasa `SimulationWindow`

**Funkcjonalność:**
- Ładowanie mapy Tiled jako tło
- Tworzenie sprite'ów dla każdej jednostki
- Renderowanie w 60 FPS
- Płynna animacja pozycji (interpolacja liniowa)
- Paski HP/morale nad jednostkami

**Synchronizacja:**
- Logika symulacji: 5 kroków/sekundę
- Renderowanie: 60 klatek/sekundę
- Usuwanie martwych jednostek w czasie rzeczywistym

### 4.4. Interfejs Webowy (`app.py`)

#### REST API Endpoints

| Endpoint | Metoda | Opis |
|----------|--------|------|
| `/` | GET | Główna strona z interfejsem |
| `/api/unit-types` | GET | Lista dostępnych typów jednostek |
| `/api/map-data` | GET | Dane mapy z Tiled |
| `/api/start-simulation` | POST | Rozpoczęcie symulacji z konfiguracją |
| `/api/stop-simulation` | POST | Zatrzymanie symulacji |
| `/api/simulation-step` | GET | Wykonanie kroku i zwrócenie stanu |
| `/api/simulation-frame` | GET | Obraz aktualnego stanu (base64) |

**Thread-safety:**
- Wykorzystanie `threading.Lock()` do synchronizacji dostępu do modelu
- Bezpieczne operacje w środowisku wielowątkowym

### 4.5. Renderer Webowy (`simulation/web_renderer.py`)

#### Klasa `WebRenderer`

**Funkcjonalność:**
- Generowanie obrazów z PIL/Pillow
- Cache sprite'ów (optymalizacja wydajności)
- Rysowanie jednostek z paskami HP/morale
- Wizualizacja stref startowych
- Fallback sprite'y gdy brak grafik

**Proces renderowania:**
1. Utworzenie obrazu tła (zielone pole)
2. Rysowanie siatki
3. Nakładanie stref startowych (półprzezroczyste)
4. Dla każdego agenta:
   - Wczytanie sprite'a (z cache)
   - Rysowanie sprite'a
   - Rysowanie pasków HP/morale

### 4.6. Frontend (`templates/index.html`)

**Struktura interfejsu:**
- **Panel lewy**: Konfiguracja jednostek (przyciski +/-)
- **Panel środkowy**: Canvas z symulacją
- **Panel prawy**: Legenda jednostek + statystyki na żywo

**Funkcjonalności:**
- Preloading sprite'ów przy starcie
- Polling API co 200ms
- Renderowanie mapy z tileset'u
- Animacje i efekty hover
- Responsywny design

---

## 5. Mechaniki Symulacji

### 5.1. System Terenu

Mapa została odtworzona w edytorze **Tiled** na podstawie map historycznych. Różne typy terenu mają różne właściwości:

| Typ Terenu | Koszt Ruchu | Bonus Obrony | Modyfikator Morale |
|-----------|-------------|--------------|-------------------|
| Równina | 1.0 | 0% | 0 |
| Las/Zarośla | 1.8 | 25% | 0 |
| Bagno/Błoto | 3.0 | -15% | -5 |
| Wzgórze | 1.5 | 15% | +5 |
| Fortyfikacje | 2.0 | 50% | +10 |
| Rzeka/Staw | ∞ | 0% | 0 |

### 5.2. System Walki

**Mechanika ataku:**
- **Strzał** (dystans 2-range):
  - 70% szans na atak, 30% na ruch
  - 60% szans trafienia
  - Obrażenia: `damage`
  - Spadek morale: `damage × 1.5`

- **Walka wręcz** (dystans ≤ 1):
  - 100% szans na atak
  - 80% szans trafienia
  - Obrażenia: `damage × 1.2`
  - Spadek morale: `damage × 2`

### 5.3. System Morale

**Kluczowy element symulacji:**
- Morale spada przy otrzymywanych obrażeniach
- Gdy morale < 25 → jednostka ucieka (stan `FLEEING`)
- Symuluje psychologiczny aspekt bitwy
- Przykład: Pospolite Ruszenie (morale: 40) szybko ucieka po 2-3 trafieniach

### 5.4. Pathfinding

**Algorytm A*:**
- Uwzględnia koszty terenu z macierzy `terrain_costs`
- Optymalizacja ścieżek
- Cache ścieżek (nie przeliczaj co krok)
- Obsługa zablokowanych ścieżek

---

## 6. Przebieg Pracy

### 6.1. Faza 1: Projektowanie i Planowanie

**Zrealizowane:**
- Analiza wymagań projektu
- Wybór technologii (Mesa, Arcade, Flask)
- Projektowanie architektury systemu
- Definicja typów jednostek i ich parametrów

### 6.2. Faza 2: Implementacja Podstawowa

**Zrealizowane:**
- Implementacja modelu symulacji (`model.py`)
- Implementacja logiki agentów (`agent.py`)
- System pathfindingu z uwzględnieniem terenu
- Mechanika walki i morale
- Wizualizacja desktopowa (Arcade)

### 6.3. Faza 3: Rozbudowa o Interfejs Webowy

**Zrealizowane:**
- Implementacja serwera Flask (`app.py`)
- REST API dla zarządzania symulacją
- Renderer webowy (`web_renderer.py`)
- Frontend HTML/CSS/JS (`templates/index.html`)
- Konfiguracja jednostek przed bitwą
- Statystyki na żywo
- Renderowanie mapy w przeglądarce

### 6.4. Faza 4: Testowanie i Debugowanie

**Zrealizowane:**
- Testowanie różnych scenariuszy bitewnych
- Naprawa błędów pathfindingu
- Optymalizacja wydajności
- Dokumentacja techniczna

### 6.5. Faza 5: Dokumentacja

**Zrealizowane:**
- README.md z instrukcją użycia
- Dokumentacja techniczna w folderze `markdowns/`
- Przykładowe scenariusze bitewne
- Przewodnik debugowania

---

## 7. Kluczowe Osiągnięcia

### 7.1. Funkcjonalne

✅ **Pełna symulacja agentowa** z realistycznymi parametrami  
✅ **Dwa tryby wizualizacji**: desktop (Arcade) i web (Canvas)  
✅ **Interaktywna konfiguracja** jednostek przed bitwą  
✅ **System pathfindingu** z uwzględnieniem terenu  
✅ **Mechanika morale** wpływająca na zachowanie jednostek  
✅ **6 różnych typów jednostek** z unikalnymi cechami  
✅ **Mapa terenu** z różnymi typami terenu  
✅ **Statystyki na żywo** podczas symulacji  

### 7.2. Techniczne

✅ **Modularna architektura** - wyraźny podział na warstwy  
✅ **Thread-safe** operacje w interfejsie webowym  
✅ **Optymalizacja wydajności** - cache sprite'ów, cache ścieżek  
✅ **Kompatybilność wsteczna** - tryb desktop nadal działa  
✅ **Dokumentacja** - szczegółowa dokumentacja techniczna  

### 7.3. Edukacyjne

✅ **Realistyczne modelowanie** - parametry oparte na danych historycznych  
✅ **Emergencja** - złożone wzorce bitwy wynikają z prostych reguł  
✅ **Wizualizacja** - łatwa obserwacja przebiegu symulacji  
✅ **Eksperymentowanie** - możliwość testowania różnych scenariuszy  

---

## 8. Przykładowe Scenariusze

### Scenariusz 1: Równowaga Sił
- Armia Koronna: 3 Piechota, 2 Dragonia, 2 Jazda, 1 Pospolite Ruszenie
- Kozacy/Tatarzy: 4 Piechota Kozacka, 4 Jazda Tatarska
- **Oczekiwany przebieg**: Długa, zacięta bitwa

### Scenariusz 2: Dominacja Kawalerii
- Armia Koronna: 8 Jazda
- Kozacy/Tatarzy: 8 Jazda Tatarska
- **Oczekiwany przebieg**: Bardzo szybkie starcie, szybkie załamanie morale

### Scenariusz 3: Test Morale
- Armia Koronna: 15 Pospolite Ruszenie (morale: 40)
- Kozacy/Tatarzy: 6 Piechota Kozacka (morale: 110)
- **Oczekiwany przebieg**: Pospolite Ruszenie szybko ucieka, zwycięstwo Kozaków

---

## 9. Napotkane Problemy i Rozwiązania

### 9.1. Problem: Pathfinding nie działał poprawnie

**Objawy:** Jednostki stały w miejscu, nie poruszały się.

**Przyczyna:** Błędne mapowanie pozycji agentów na siatkę pathfindingu.

**Rozwiązanie:** 
- Poprawiono funkcję `get_pos_tuple()` w klasie `MilitaryAgent`
- Dodano walidację pozycji przed obliczeniem ścieżki
- Dodano obsługę zablokowanych ścieżek

### 9.2. Problem: Martwe jednostki pozostawały na mapie

**Objawy:** Jednostki z HP <= 0 nadal były renderowane.

**Przyczyna:** Brak mechanizmu czyszczenia martwych agentów.

**Rozwiązanie:**
- Dodano metodę `cleanup_dead_agents()` w modelu
- Wywoływanie czyszczenia po każdym kroku symulacji
- Synchronizacja usuwania sprite'ów w wizualizacji

### 9.3. Problem: Niska wydajność w interfejsie webowym

**Objawy:** Opóźnienia w renderowaniu, niska płynność.

**Przyczyna:** Brak cache'owania sprite'ów, przeliczanie ścieżek co krok.

**Rozwiązanie:**
- Implementacja cache sprite'ów w `WebRenderer`
- Cache ścieżek w agentach (nie przeliczaj jeśli cel się nie zmienił)
- Optymalizacja polling'u (200ms zamiast 100ms)

---

## 10. Możliwy Dalszy Rozwój

### 10.1. Funkcjonalności

- [ ] **Scenariusze historyczne** - początkowe rozstawienie wojsk z 15 sierpnia
- [ ] **Łańcuch dowodzenia** - agenci-dowódcy wpływający na morale pobliskich jednostek
- [ ] **System logistyki** - zaopatrzenie w amunicję, żywność
- [ ] **Zaawansowane taktyki** - flankowanie, formacje
- [ ] **System pogody** - wpływ deszczu, mgły na widoczność i skuteczność
- [ ] **Replay system** - zapis i odtwarzanie bitew
- [ ] **Export do wideo** - generowanie MP4 z bitwy
- [ ] **Multiplayer mode** - 2 graczy vs
- [ ] **AI opponent** - komputer dobiera jednostki

### 10.2. Techniczne

- [ ] **WebSocket** - zamiast polling (lepsza wydajność)
- [ ] **Zaawansowane statystyki** - wykresy, heatmapy
- [ ] **Save/Load scenarios** - zapisywanie konfiguracji
- [ ] **Mobile support** - responsywny design dla urządzeń mobilnych
- [ ] **Unit tests** - testy jednostkowe dla kluczowych komponentów
- [ ] **Performance profiling** - optymalizacja wydajności

### 10.3. Wizualizacja

- [ ] **Efekty terenu** - animacje, wizualizacja kosztów ruchu
- [ ] **Mini-mapa** - przegląd całego pola bitwy
- [ ] **Sound effects** - dźwięki walki, marszu
- [ ] **Particle effects** - efekty wybuchów, dymu

---

## 11. Wnioski

### 11.1. Osiągnięcia

Projekt z powodzeniem zrealizował założone cele:
- Stworzono funkcjonalną symulację agentową bitwy historycznej
- Zaimplementowano realistyczne mechaniki walki i morale
- Zbudowano dwa interfejsy użytkownika (desktop i web)
- Opracowano dokumentację techniczną

### 11.2. Wnioski Techniczne

- **Mesa** okazała się doskonałym wyborem dla modelowania agentowego
- **Modularna architektura** ułatwiła rozbudowę o interfejs webowy
- **Pathfinding z uwzględnieniem terenu** znacznie zwiększa realizm symulacji
- **System morale** jest kluczowy dla realistycznego modelowania bitwy

### 11.3. Wnioski Metodologiczne

- **Emergencja** - złożone wzorce bitwy wynikają z prostych reguł jednostek
- **Heterogeniczność** - różne typy jednostek tworzą interesujące interakcje
- **Wizualizacja** - kluczowa dla zrozumienia przebiegu symulacji
- **Eksperymentowanie** - możliwość testowania różnych scenariuszy jest bardzo wartościowa

### 11.4. Wartość Edukacyjna

Projekt demonstruje:
- Zastosowanie paradygmatu systemów dyskretnych w modelowaniu historycznym
- Wykorzystanie frameworków do modelowania agentowego
- Integrację różnych technologii (Python, web, wizualizacja)
- Praktyczne zastosowanie algorytmów (A*, FSM)

---

## 12. Podsumowanie

Projekt **Symulacja Bitwy pod Zborowem (1649)** to kompleksowa implementacja agentowej symulacji historycznej bitwy, wykorzystująca nowoczesne technologie i frameworki. System umożliwia nie tylko wizualizację przebiegu bitwy, ale również eksperymentowanie z różnymi scenariuszami i analizę wpływu różnych czynników na wynik starcia.

Projekt został zrealizowany z wykorzystaniem profesjonalnych narzędzi i najlepszych praktyk programistycznych, co zaowocowało modularną, rozszerzalną architekturą gotową do dalszego rozwoju.

---

## 13. Bibliografia i Źródła

### Źródła Historyczne
- Kucharski, W. - prace dotyczące Bitwy pod Zborowem
- Mandzy, A. - opracowania historyczne

### Dokumentacja Techniczna
- Mesa Documentation: https://mesa.readthedocs.io/
- Arcade Documentation: https://api.arcade.academy/
- Flask Documentation: https://flask.palletsprojects.com/
- Tiled Map Editor: https://www.mapeditor.org/

### Zależności Projektu
- Wszystkie zależności wymienione w `requirements.txt`

---

**Autorzy projektu:**  
Patrick Bajorski, Jan Banasik, Gabriel Filipowicz

**Data zakończenia:** 2024

**Przedmiot:** Symulacja Systemów Dyskretnych

