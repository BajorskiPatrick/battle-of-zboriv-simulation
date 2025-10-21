# 🌐 Interfejs Webowy - Instrukcja Użycia

## 🚀 Uruchomienie Interfejsu Webowego

### 1. Instalacja zależności

Jeśli jeszcze nie zainstalowałeś wszystkich pakietów, uruchom:

```bash
pip install -r requirements.txt
```

### 2. Uruchomienie serwera Flask

```bash
python app.py
```

Serwer uruchomi się domyślnie na `http://localhost:5000`

### 3. Otwórz przeglądarkę

Przejdź do: **http://localhost:5000**

---

## 🎮 Jak Korzystać z Interfejsu

### Panel Konfiguracji Jednostek (Lewy)

1. **Wybierz jednostki dla Armii Koronnej** (czerwona sekcja):
   - Piechota
   - Dragonia
   - Jazda
   - Pospolite Ruszenie

2. **Wybierz jednostki dla Kozaków i Tatarów** (niebieska sekcja):
   - Piechota Kozacka
   - Jazda Tatarska

3. **Ustaw ilość jednostek**:
   - Użyj przycisków `+` / `-`
   - Lub wpisz wartość bezpośrednio (0-20 jednostek każdego typu)

4. **Kliknij "Rozpocznij Symulację"**

### Panel Symulacji (Środek)

- Symulacja wyświetla się w czasie rzeczywistym
- **Kolory jednostek**:
  - 🔴 Czerwone = Armia Koronna
  - 🔵 Niebieskie = Kozacy/Tatarzy
- **Paski nad jednostkami**:
  - Zielony = HP (punkty życia)
  - Cyjan = Morale (duch walki)

### Panel Legendy (Prawy)

- **Legenda jednostek** z ikonkami i parametrami:
  - HP (wytrzymałość)
  - Morale (odporność psychiczna)
  - Zasięg (dystans ataku)
  - Atak (siła obrażeń)

- **Statystyki na żywo**:
  - Liczba żywych jednostek Armii Koronnej
  - Liczba żywych jednostek Kozaków/Tatarów
  - Łączna liczba jednostek

---

## ⚔️ Przykładowe Scenariusze

### Scenariusz 1: Bitwa Zrównoważona
- Armia Koronna: 3 Piechota, 2 Jazda
- Kozacy/Tatarzy: 3 Piechota Kozacka, 2 Jazda Tatarska

### Scenariusz 2: Przewaga Kawalerii
- Armia Koronna: 2 Piechota, 5 Jazda
- Kozacy/Tatarzy: 2 Piechota Kozacka, 5 Jazda Tatarska

### Scenariusz 3: Masa Pospolitego Ruszenia
- Armia Koronna: 10 Pospolite Ruszenie
- Kozacy/Tatarzy: 5 Piechota Kozacka

### Scenariusz 4: Elitarne Jednostki
- Armia Koronna: 3 Dragonia, 3 Jazda
- Kozacy/Tatarzy: 6 Jazda Tatarska

---

## 🎯 Co Obserwować

1. **Mobilność**: Jazda Tatarska (prędkość 4) vs Jazda Koronna (prędkość 3)
2. **Morale**: Pospolite Ruszenie (40) vs Piechota Kozacka (110)
3. **Zasięg**: Jazda Tatarska (zasięg 7) może atakować z daleka
4. **Obrażenia**: Jazda Koronna (20 damage) w walce wręcz jest śmiertelna

---

## 🛑 Zatrzymanie Symulacji

Kliknij **"Zatrzymaj Symulację"** aby zakończyć bieżącą bitwę.

---

## 🖥️ Tryb Desktop (Alternatywa)

Aby uruchomić oryginalny tryb desktop z Arcade:

```bash
python main.py
```

(Używa domyślnego scenariusza bez konfiguracji)

---

## 💡 Wskazówki

- **Różnorodność**: Mieszaj różne typy jednostek dla lepszej taktyki
- **Balans**: Zbyt wiele słabych jednostek (Pospolite Ruszenie) może szybko uciekać
- **Obserwuj morale**: Jednostki z niskim morale uciekają gdy < 25
- **Testy strategii**: Eksperymentuj z różnymi kombinacjami!

---

## 🐛 Rozwiązywanie Problemów

**Problem**: Serwer się nie uruchamia
- Sprawdź czy zainstalowałeś `flask` i `flask-cors`
- Uruchom: `pip install flask flask-cors pillow`

**Problem**: Nie widać sprite'ów
- Upewnij się że folder `assets/sprites/` zawiera pliki PNG
- Sprawdź ścieżki w `simulation/model.py`

**Problem**: Symulacja nie startuje
- Sprawdź konsolę przeglądarki (F12) dla błędów JavaScript
- Upewnij się że dodałeś przynajmniej jedną jednostkę

---

Miłej zabawy z symulacją! ⚔️🏹
