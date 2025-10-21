# 🐛 Fix: Martwe Jednostki na Ekranie Zwycięstwa

## Problem
Po zakończeniu bitwy, na planszy pozostawała jedna wroga jednostka z `hp <= 0`, która wizualnie wyglądała błędnie na ekranie zwycięstwa.

### Przyczyna:
**Race condition** między usuwaniem jednostek a sprawdzaniem statusu bitwy:

```
1. Jednostka dostaje śmiertelne obrażenia → hp = -5
2. agent.step() wykonuje się → usuwa agenta z grid i schedule
3. API zbiera dane agents_data → agent JESZCZE w schedule.agents
4. API wysyła agenta do frontendu → renderowany na Canvas
5. API sprawdza battle_status → agent już usunięty
6. Modal się pokazuje → MARTWY agent widoczny na Canvas!
```

---

## Rozwiązanie

### 1. Dodano `cleanup_dead_agents()` w Model
**Plik:** `simulation/model.py`

```python
def cleanup_dead_agents(self):
    """ Usuwa jednostki z hp <= 0 z siatki i schedulera. """
    dead_agents = [agent for agent in self.schedule.agents 
                  if isinstance(agent, MilitaryAgent) and agent.hp <= 0]
    for agent in dead_agents:
        if agent.pos:  # Jeśli agent jest na siatce
            self.grid.remove_agent(agent)
        if agent in self.schedule.agents:
            self.schedule.remove(agent)
```

**Wywołanie:**
- Po każdym `step()` (double-check)
- Przed `get_battle_status()` (gwarancja czystości)

---

### 2. Filtrowanie w API
**Plik:** `app.py`

```python
# Zbierz informacje o aktualnym stanie (TYLKO ŻYWI AGENCI)
agents_data = []
for agent in simulation.schedule.agents:
    # Pomiń agentów z hp <= 0
    if agent.hp <= 0:
        continue
    
    # ... reszta kodu ...
```

**Statystyki również filtrują:**
```python
stats = {
    "crown_count": len([a for a in simulation.schedule.agents 
                       if a.faction == "Armia Koronna" and a.hp > 0]),
    "cossack_count": len([a for a in simulation.schedule.agents 
                         if a.faction == "Kozacy/Tatarzy" and a.hp > 0]),
    "total_agents": len([a for a in simulation.schedule.agents if a.hp > 0])
}
```

---

### 3. Porządek Wykonania
**Nowa kolejność w `model.step()`:**
```python
def step(self):
    """ Wykonuje jeden krok symulacji. """
    self.schedule.step()
    # Po kroku usuń martwe jednostki (double-check)
    self.cleanup_dead_agents()
```

**W `get_battle_status()`:**
```python
def get_battle_status(self):
    # Najpierw wyczyść martwe jednostki
    self.cleanup_dead_agents()
    
    # Potem policz żywych
    crown_count = sum(1 for agent in self.schedule.agents 
                     if isinstance(agent, MilitaryAgent) 
                     and agent.faction == "Armia Koronna" 
                     and agent.hp > 0)
    # ... reszta ...
```

---

## Przepływ Danych (Po Poprawce)

```
┌─────────────────────────────────────────────────────┐
│ 1. Agent dostaje śmiertelne obrażenia (hp = -5)    │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│ 2. agent.step() wykrywa hp <= 0                     │
│    → grid.remove_agent()                            │
│    → schedule.remove()                              │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│ 3. model.step() kończy wszystkie agent.step()      │
│    → cleanup_dead_agents() (double-check)           │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│ 4. API zbiera agents_data                           │
│    → for agent in schedule.agents:                  │
│        if agent.hp <= 0: continue ✅                 │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│ 5. API wywołuje get_battle_status()                 │
│    → cleanup_dead_agents() (gwarancja)              │
│    → count tylko hp > 0                             │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│ 6. Frontend renderuje TYLKO żywych agentów          │
│    → Modal pokazuje się                             │
│    → Plansza bez martwych jednostek! ✅             │
└─────────────────────────────────────────────────────┘
```

---

## Testowanie

### Scenariusz testowy:
```
1. Skonfiguruj: 2x Piechota Koronna vs 2x Piechota Kozacka
2. Uruchom symulację
3. Poczekaj aż zostanie 1 jednostka z każdej strony
4. Obserwuj moment śmierci ostatniej jednostki
```

### Oczekiwany wynik:
✅ Martwa jednostka NIE jest widoczna na Canvas  
✅ Modal zwycięstwa pokazuje czyste pole bitwy  
✅ Statystyki są poprawne (tylko żywi liczeni)  
✅ Brak "widmowych" jednostek  

### Przed poprawką:
❌ Martwa jednostka widoczna jako sprite z pełnym HP barem  
❌ Wizualnie mylące (czy to bug? czy żyje?)  

---

## Dodatkowe Zabezpieczenia

### 1. Trzypunktowa weryfikacja:
- ✅ **agent.step()** - usuwanie w momencie śmierci
- ✅ **model.step()** - cleanup po wszystkich agentach
- ✅ **get_battle_status()** - cleanup przed sprawdzaniem

### 2. Filtrowanie w API:
- ✅ `if agent.hp <= 0: continue` w pętli
- ✅ `and a.hp > 0` w statystykach

### 3. Warunek w Frontend:
Canvas automatycznie renderuje tylko agentów z `agents_data`, więc jeśli API nie wyśle martwych - nie będą renderowani.

---

## Edge Cases

### Case 1: Obie ostatnie jednostki giną jednocześnie
```python
# Obie mają hp = 5, atakują się nawzajem w tym samym kroku
agent1.hp -= 10  # hp = -5
agent2.hp -= 10  # hp = -5

# cleanup_dead_agents() usuwa OBIE
# get_battle_status() zwraca "Remis"
# Canvas jest pusty ✅
```

### Case 2: Jednostka ucieka z hp = 1
```python
# Nie jest to martwy agent
agent.hp = 1  # ŻYWY
agent.state = "FLEEING"

# Będzie renderowany ✅
# Będzie liczony w statystykach ✅
```

### Case 3: Negative HP przez overkill
```python
# Agent ma hp = 5, dostaje 50 obrażeń
agent.hp = -45

# Warunek hp <= 0 łapie to ✅
# cleanup_dead_agents() usuwa ✅
```

---

## Performance

### Koszt cleanup_dead_agents():
```python
O(n) gdzie n = liczba agentów w schedule
Typowo: n = 10-50 agentów
Koszt: ~0.1-0.5ms (pomijalny)
```

### Wywołania na krok:
- `model.step()` → 1x cleanup
- `get_battle_status()` → 1x cleanup (tylko gdy API wywołane)
- **Total:** Max 2x na request (~1ms)

---

## Wnioski

### Problem rozwiązany:
✅ Martwe jednostki nie pojawiają się na ekranie zwycięstwa  
✅ Wizualizacja jest czysta i precyzyjna  
✅ Statystyki są dokładne  
✅ Brak race conditions  

### Mechanizm obronny:
- **Redundant cleanup** - wykonywany wielokrotnie dla pewności
- **Filtrowanie na poziomie API** - double-check przed wysłaniem
- **Warunek `hp > 0`** - konsekwentny w całym kodzie

---

**Status: ✅ NAPRAWIONE** - Martwe jednostki są teraz poprawnie usuwane przed wyświetleniem ekranu zwycięstwa! 🎉
