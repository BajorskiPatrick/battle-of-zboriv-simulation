# Symulacja Agentowa: Bitwa pod Zborowem (1649)

## 1. Wprowadzenie

Projekt ten jest agentową symulacją historycznej Bitwy pod Zborowem, która odbyła się w dniach 15-16 sierpnia 1649 roku. Jest to implementacja założeń z dokumentu "Szczegółowy opis projektu", wykorzystująca dane ze źródeł historycznych (m.in. prace W. Kucharskiego i A. Mandzy'ego) do modelowania dynamiki starcia w paradygmacie systemów dyskretnych.

Celem projektu jest nie tylko wizualizacja przebiegu bitwy, ale również stworzenie narzędzia do analizy "co by było gdyby", pozwalającego badać wpływ kluczowych czynników (morale, teren, pogoda, skuteczność uzbrojenia) na ostateczny wynik starcia.

### Demo


## 2. Zastosowane Technologie

Symulacja została zbudowana w oparciu o profesjonalny i nowoczesny stack technologiczny w ekosystemie Pythona, z wyraźnym oddzieleniem logiki od wizualizacji.

*   **Język programowania:** Python 3.9+
*   **Silnik symulacji agentowej:** [**Mesa**](https://mesa.readthedocs.io/en/stable/) - framework dedykowany do modelowania agentowego (ABM), zarządzający harmonogramem, przestrzenią i stanem agentów.
*   **Silnik wizualizacji 2D:** [**Arcade**](https://api.arcade.academy/) - nowoczesna biblioteka do tworzenia gier i wizualizacji 2D, oferująca wysoką wydajność i wbudowane wsparcie dla map kafelkowych.
*   **Tworzenie i obsługa mapy:**
    *   [**Tiled Map Editor**](https://www.mapeditor.org/) - edytor do tworzenia map kafelkowych, w którym zdefiniowano topografię pola bitwy i właściwości terenu.
    *   [**Pytmx**](https://pytmx.readthedocs.io/en/latest/) - biblioteka do parsowania danych z mapy `.tmx` na potrzeby silnika symulacji.
*   **Obliczenia:** [**NumPy**](https://numpy.org/) - do wydajnych operacji na siatce kosztów ruchu.
*   **Pathfinding:** [**Pathfinding**](https://pypi.org/project/pathfinding/) - do znajdowania optymalnych ścieżek dla agentów na mapie.

## 3. Instalacja i Uruchomienie

1.  **Sklonuj repozytorium:**
    ```bash
    git clone [URL_TWOJEGO_REPOZYTORIUM]
    cd zborow_simulation
    ```

2.  **Stwórz i aktywuj wirtualne środowisko (zalecane):**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Zainstaluj wymagane biblioteki:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Uruchom symulację:**
    ```bash
    python main.py
    ```

## 4. Struktura Projektu

Projekt ma logiczną, modułową strukturę ułatwiającą rozwój i konserwację.

```
zborow_simulation/
├── assets/
│   ├── map/
│   │   ├── zborow_battlefield.tmx   # Plik mapy Tiled
│   │   └── tileset.png            # Zestaw kafelków graficznych
│   └── sprites/
│       ├── crown_dragoon.png
│       ├── crown_cavalry.png
│       └── ... (grafiki dla wszystkich jednostek)
├── simulation/
│   ├── agent.py                 # Definicja klasy Agenta (MilitaryAgent)
│   ├── model.py                 # Główny model symulacji (BattleOfZborowModel)
│   └── utils.py                 # Funkcje pomocnicze
├── visualization/
│   ├── window.py                # Główne okno aplikacji Arcade
│   └── sprites.py               # Niestandardowe klasy sprajtów (np. z paskiem zdrowia)
├── main.py                        # Punkt startowy aplikacji
├── requirements.txt               # Lista zależności
└── README.md                      # Ten plik
```

## 5. Szczegółowy Opis Modelu

Model symulacji został wiernie oparty na dostarczonej specyfikacji.

### 5.1. Środowisko: Pole Bitwy

Mapa została odtworzona w edytorze **Tiled** na podstawie map historycznych z prac W. Kucharskiego i A. Mandzy'ego. Kluczowe elementy topograficzne (rzeka Strypa, bagna, wzgórza) zostały uwzględnione poprzez przypisanie niestandardowych właściwości do kafelków terenu.

| Typ Terenu      | Koszt Ruchu | Bonus do Obrony | Modyfikator Morale | Opis                                           |
|-----------------|-------------|-----------------|--------------------|------------------------------------------------|
| **Równina**     | 1.0         | 0%              | 0                  | Domyślny teren, brak modyfikatorów.            |
| **Las/Zarośla** | 1.8         | 25%             | 0                  | Ogranicza widoczność, zapewnia osłonę.         |
| **Bagno/Błoto** | 3.0         | -15%            | -5                 | Znacznie spowalnia ruch, negatywnie wpływa na morale. |
| **Wzgórze**     | 1.5         | 15%             | +5                 | Trudniejszy do pokonania, ale daje bonus w obronie. |
| **Fortyfikacje**| 2.0         | 50%             | +10                | Wały ziemne, znaczący bonus obronny.           |
| **Rzeka/Staw**  | ∞ (nieprzekraczalny) | 0%              | 0                  | Bariera naturalna, przekraczalna tylko w brodach. |

Dodatkowo, symulacja uwzględnia **globalne warunki pogodowe** (deszcz), które wpływają na wszystkich agentów poprzez:
*   Zmniejszenie skuteczności broni palnej (większa szansa na niewypał).
*   Ograniczenie widoczności.
*   Negatywny wpływ na morale (jeśli jednostki nie są do tego przyzwyczajone).

### 5.2. Agenci: Jednostki Wojskowe

Każdy agent na mapie reprezentuje oddział wojskowy liczący ok. 50 żołnierzy. Posiada zestaw atrybutów (`zdrowie`, `morale`, `amunicja`, `status`) oraz unikalne cechy wynikające z jego typu.

#### Frakcja: Armia Koronna

| Typ Jednostki      | Uzbrojenie             | Cechy Specjalne                                                              |
|--------------------|------------------------|------------------------------------------------------------------------------|
| **Piechota**       | Muszkiet, Pika         | + Wysoka dyscyplina i morale. <br> + Odporność na szarże kawalerii.             |
| **Dragonia**       | Broń palna             | + Mobilna jednostka, może walczyć pieszo.                                    |
| **Jazda**          | Szabla, lanca, broń palna| + Wysoka prędkość. <br> + Potężny bonus do szarży (pierwszego ataku).         |
| **Pospolite Ruszenie**| Mieszane            | - Bardzo niskie morale początkowe. <br> - Wysoka podatność na panikę i ucieczkę. |

#### Frakcja: Kozacy i Tatarzy

| Typ Jednostki        | Uzbrojenie        | Cechy Specjalne                                                                       |
|----------------------|-------------------|---------------------------------------------------------------------------------------|
| **Piechota Kozacka** | Samopał (muszkiet)| + Wysoka determinacja (odporność na spadek morale). <br> + Szybsze ładowanie broni.   |
| **Jazda Tatarska**   | Łuk, szabla       | + Najwyższa szybkostrzelność. <br> + Broń niezawodna w deszczu. <br> + Bardzo mobilna. |

### 5.3. Mechanika i Logika

*   **System Czasu:** Symulacja działa w dyskretnych krokach czasowych (tyknięciach).
*   **Sztuczna Inteligencja (FSM):** Zachowanie agentów jest sterowane przez prostą maszynę stanów (Finite State Machine):
    1.  **PATROL / OCZEKIWANIE:** Agent przemieszcza się w stronę wyznaczonego celu lub utrzymuje pozycję.
    2.  **ATAK:** Po wykryciu wroga w zasięgu, agent przechodzi do stanu ataku.
    3.  **RUCH DO CELU:** Jeśli wróg jest widoczny, ale poza zasięgiem, agent porusza się w jego kierunku.
    4.  **UCIECZKA:** Jeśli morale spadnie poniżej krytycznego progu, agent panikuje i wycofuje się z walki w bezpieczne miejsce.
*   **System Walki:** Wynik starcia jest stochastyczny. Szansa na trafienie zależy od:
    *   Bazowej celności jednostki.
    *   Dystansu do celu.
    *   Osłony, jaką zapewnia teren.
    *   Warunków pogodowych.
    Trafienie obniża `zdrowie` (liczebność oddziału) i `morale` celu.
*   **System Morale:** Kluczowy element symulacji. Morale jednostki zmienia się dynamicznie:
    *   **Spada:** przy ponoszeniu strat, byciu pod ostrzałem, kontakcie z przytłaczającym wrogiem, złej pogodzie.
    *   **Rośnie:** przy zadawaniu strat wrogowi, wygrywaniu starć.
    Drastyczny spadek morale prowadzi do paniki i ucieczki.

## 6. Ograniczenia i Możliwy Dalszy Rozwój

Model jest celowo uproszczony, aby skupić się na kluczowych mechanikach.
*   **Uproszczenia:** Łańcuch dowodzenia jest pominięty (agenci działają autonomicznie), logistyka jest ograniczona do początkowej amunicji.
*   **Możliwy rozwój:**
    *   Implementacja **scenariuszy historycznych** (np. początkowe rozstawienie wojsk z 15 sierpnia).
    *   Dodanie **łańcucha dowodzenia** (agenci-dowódcy wpływający na morale pobliskich jednostek).
    *   Rozbudowa systemu **zbierania i analizy danych** (za pomocą `mesa.DataCollector`) w celu badania wrażliwości modelu na parametry.
    *   Wprowadzenie bardziej zaawansowanych zachowań taktycznych (flankowanie, formacje).

---
Autorzy oryginalnej koncepcji: Patrick Bajorski, Jan Banasik, Gabriel Filipowicz
Implementacja w Pythonie: [Twoje Imię/Nazwa]