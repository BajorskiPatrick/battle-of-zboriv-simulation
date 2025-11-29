# Symulacja Agentowa: Bitwa pod Zborowem (1649)

Projekt ten jest zaawansowaną symulacją agentową historycznej Bitwy pod Zborowem (1649). Wykorzystuje paradygmat modelowania agentowego (ABM) do odwzorowania zachowań poszczególnych oddziałów wojskowych, ich interakcji oraz wpływu terenu i pogody na przebieg starcia.

## 1. Charakterystyka Jednostek

W symulacji zaimplementowano szereg historycznych typów jednostek, z których każda posiada unikalny zestaw cech wpływających na jej skuteczność bojową.

### Parametry Jednostek
Każdy agent (oddział) opisany jest przez następujące zmienne:
*   **HP (Punkty Życia):** Wytrzymałość oddziału. Spadek do 0 oznacza zniszczenie.
*   **Morale:** Wola walki. Niskie morale prowadzi do paniki i ucieczki.
*   **Dyscyplina:** Odporność na spadki morale i szansa na opanowanie paniki.
*   **Atak Wręcz / Dystansowy:** Siła zadawanych obrażeń.
*   **Zasięg:** Odległość, z jakiej jednostka może atakować.
*   **Amunicja:** Liczba strzałów dla jednostek dystansowych.
*   **Obrona:** Redukcja otrzymywanych obrażeń.
*   **Szybkość:** Bazowa prędkość poruszania się.

### Typy Jednostek

#### Armia Koronna
| Jednostka | Rola | Cechy Szczególne |
|-----------|------|------------------|
| **Husaria** | Ciężka jazda przełamująca | Ogromne morale i dyscyplina, bonus do szarży, wysoka obrona. |
| **Pancerni** | Jazda uniwersalna | Dobry balans między mobilnością a siłą uderzenia. |
| **Rajtaria** | Jazda z bronią palną | Posiada broń palną (krótki zasięg), solidna w zwarciu. |
| **Dragonia** | Piechota konna | Mobilni strzelcy, walczą dystansowo. |
| **Piechota Niemiecka** | Elitarna piechota | Bardzo wysoka dyscyplina, silny ogień, powolna. |
| **Pospolite Ruszenie** | Posiłki | Niska dyscyplina, łatwo wpadają w panikę, słabe uzbrojenie. |
| **Artyleria Koronna** | Wsparcie ogniowe | Ogromny zasięg i obrażenia, bardzo powolna, bezbronna w zwarciu. |

#### Kozacy i Tatarzy
| Jednostka | Rola | Cechy Szczególne |
|-----------|------|------------------|
| **Jazda Tatarska** | Lekka jazda | Bardzo szybka, atakuje z łuków, unika zwarcia. |
| **Piechota Kozacka** | Strzelcy wyborowi | Wysokie obrażenia dystansowe, solidne morale. |
| **Jazda Kozacka** | Jazda średnia | Przyzwoita w zwarciu, wspiera piechotę. |
| **Czern** | Pospólstwo | Liczna, ale słaba i tchórzliwa. Mięso armatnie. |
| **Artyleria Kozacka** | Ostrzał obozu | Mniejsza siła niż koronna, ale wciąż groźna. |

---

## 2. Mechanika Symulacji i Działanie Agentów

Sercem symulacji jest cykl decyzyjny agenta (`step`), który wykonuje się w każdej turze dla każdego oddziału.

### Cykl Decyzyjny Agenta
1.  **Test Morale i Panika:**
    *   Jeśli `morale` spadnie poniżej progu paniki (obliczanego jako `25 - (dyscyplina / 5)`), agent wykonuje test dyscypliny.
    *   Niepowodzenie oznacza przejście w stan **FLEEING** (Ucieczka). Agent ignoruje rozkazy i ucieka najkrótszą drogą do krawędzi mapy.
2.  **Wykrywanie Wroga:**
    *   Agent skanuje otoczenie w promieniu wzroku (zależnym od pogody: 20 pól normalnie, 6 we mgle).
    *   Wybiera najbliższego wroga jako cel.
3.  **Walka:**
    *   **Dystansowa:** Jeśli wróg jest w zasięgu i agent ma amunicję.
        *   Szansa na strzał zależy od pogody (deszcz zwiększa ryzyko niewypału).
        *   Obrażenia są redukowane przez teren, na którym stoi cel (osłona).
    *   **Wręcz:** Jeśli wróg jest na sąsiednim polu (dystans <= 1.5).
        *   Jednostki jazdy (np. Husaria) otrzymują bonus do obrażeń (szarża).
4.  **Ruch:**
    *   Jeśli brak wroga w zasięgu wzroku, agent kieruje się ku **Celowi Strategicznemu** (losowy punkt w głębi terytorium wroga).
    *   Jeśli wróg jest widoczny, ale poza zasięgiem, agent wyznacza ścieżkę do niego.

### System Obliczeń
*   **Otrzymywanie Obrażeń:**
    ```python
    redukcja = min(obrażenia - 1, losowa(0, obrona // 2))
    faktyczne_obrażenia = max(1, obrażenia - redukcja)
    hp -= faktyczne_obrażenia
    ```
*   **Utrata Morale:**
    Jest proporcjonalna do otrzymanych obrażeń. Jednostki o wysokiej dyscyplinie (>80) tracą morale wolniej (mnożnik 0.7).

### Ruch i Pathfinding
*   Wykorzystywany jest algorytm **A* (A-Star)** do znajdowania optymalnej ścieżki.
*   Mapa podzielona jest na kafelki o różnym **koszcie ruchu**:
    *   Trawa: koszt 1.0
    *   Las/Wzgórza: koszt > 1.0 (spowalnia)
    *   Woda/Przeszkody: koszt bardzo wysoki lub nieprzekraczalny.
*   Szansa na wykonanie ruchu w turze zależy od szybkości jednostki i trudności terenu:
    `szansa_ruchu = speed / (koszt_terenu * 5.0)`
    Oznacza to, że ciężkie jednostki mogą "grzęznąć" w trudnym terenie.

### Wpływ Pogody
Symulacja uwzględnia zmienne warunki atmosferyczne, które globalnie wpływają na rozgrywkę:
1.  **Deszcz (Rain):**
    *   **Błoto:** Koszt ruchu na zwykłym terenie drastycznie rośnie (x2.5). Jazda i artyleria stają się bardzo powolne.
    *   **Mokry Proch:** Obrażenia jednostek strzeleckich (poza łucznikami) spadają o 70%. Zwiększa się szansa na niewypał.
2.  **Mgła (Fog):**
    *   Ogranicza zasięg widzenia jednostek z 20 do 6 pól, wymuszając walkę na krótki dystans.

---

## 3. Aspekty Techniczne

Projekt został zrealizowany w języku **Python** z wykorzystaniem nowoczesnych bibliotek do symulacji i wizualizacji.

### Architektura
*   **Backend (Symulacja):** Oparty na frameworku **Mesa**. Odpowiada za logikę agentów, zarządzanie stanem świata i harmonogramowanie tur.
*   **Frontend (Wizualizacja):** Interfejs webowy zbudowany we frameworku **Flask**. Komunikuje się z backendem, pobierając stan agentów i renderując go na mapie w przeglądarce.

### Kluczowe Biblioteki
*   `Mesa`: Silnik symulacji agentowej (Agent-Based Modeling).
*   `NumPy`: Wydajne operacje macierzowe na siatce terenu (mapa kosztów).
*   `Pathfinding`: Biblioteka realizująca algorytm A* na siatce nawigacyjnej.
*   `PyTMX`: Obsługa map stworzonych w edytorze **Tiled** (.tmx). Pozwala na odczytywanie warstw terenu i właściwości kafelków.

### Struktura Plików
*   `simulation/agent.py`: Logika decyzyjna pojedynczego oddziału.
*   `simulation/model.py`: Główna klasa symulacji, inicjalizacja mapy i jednostek.
*   `app.py`: Serwer Flask obsługujący interfejs webowy.
*   `assets/`: Grafiki jednostek i pliki mapy.

## 4. Uruchomienie

1.  Zainstaluj wymagane biblioteki:
    ```bash
    pip install -r requirements.txt
    ```
2.  Uruchom aplikację webową:
    ```bash
    python app.py
    ```
3.  Otwórz przeglądarkę pod adresem: `http://127.0.0.1:5000`
