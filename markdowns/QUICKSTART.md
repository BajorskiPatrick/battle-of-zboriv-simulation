# 🚀 Quick Start - Interfejs Webowy

## Szybkie uruchomienie w 3 krokach:

### 1️⃣ Zainstaluj zależności
```bash
pip install -r requirements.txt
```

### 2️⃣ Uruchom serwer
```bash
python app.py
```

### 3️⃣ Otwórz przeglądarkę
```
http://localhost:5000
```

---

## 🎮 Jak używać:

1. **Wybierz jednostki** (lewy panel):
   - Użyj przycisków +/- aby dodać jednostki
   - Możesz wybrać 0-20 jednostek każdego typu

2. **Kliknij "Rozpocznij Symulację"**

3. **Obserwuj bitwę** (środkowy panel):
   - 🔴 Czerwone = Armia Koronna
   - 🔵 Niebieskie = Kozacy/Tatarzy
   - Zielony pasek = HP
   - Cyjan pasek = Morale

4. **Sprawdź legendę** (prawy panel):
   - Ikony wszystkich jednostek
   - Parametry (HP, Morale, Zasięg, Atak)
   - Statystyki na żywo

---

## 💡 Przykładowy scenariusz testowy:

```
Armia Koronna:
- Piechota: 3
- Jazda: 2

Kozacy/Tatarzy:
- Piechota Kozacka: 3
- Jazda Tatarska: 2

→ Kliknij "Rozpocznij Symulację"
```

---

## 🆘 Problemy?

**Port zajęty?**
```bash
# Zmień port w app.py (ostatnia linia):
app.run(debug=True, host='0.0.0.0', port=5001)
```

**Brak sprite'ów?**
- Upewnij się że folder `assets/sprites/` istnieje
- Interfejs użyje kolorowych kwadratów jako fallback

**Symulacja nie startuje?**
- Sprawdź konsolę przeglądarki (F12)
- Sprawdź terminal gdzie uruchomiłeś `python app.py`

---

## 📚 Więcej informacji:

- Pełna dokumentacja: [README_WEB.md](README_WEB.md)
- Instrukcje użytkowania: [WEB_INTERFACE.md](WEB_INTERFACE.md)
- Opis logiki symulacji: [summary.md](summary.md)

---

Miłej zabawy! ⚔️
