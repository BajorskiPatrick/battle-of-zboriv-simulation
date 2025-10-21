# 📊 Przykładowe Scenariusze Bitewne

Ten dokument zawiera gotowe konfiguracje jednostek do testowania różnych sytuacji taktycznych.

---

## 🎯 Scenariusz 1: Równowaga Sił
**Cel:** Zbilansowana bitwa między armiami

### Konfiguracja:
```
Armia Koronna:
├── Piechota: 3
├── Dragonia: 2
├── Jazda: 2
└── Pospolite Ruszenie: 1

Kozacy/Tatarzy:
├── Piechota Kozacka: 4
└── Jazda Tatarska: 4
```

### Oczekiwany przebieg:
- Długa, zacięta bitwa
- Przewaga mobilności po stronie Kozaków (Jazda Tatarska speed: 4)
- Armia Koronna silniejsza w starciu bezpośrednim
- **Zwycięzca:** Nieprzewidywalny (zależy od morale i szczęścia)

---

## ⚔️ Scenariusz 2: Dominacja Kawalerii
**Cel:** Test mobilnych jednostek

### Konfiguracja:
```
Armia Koronna:
└── Jazda: 8

Kozacy/Tatarzy:
└── Jazda Tatarska: 8
```

### Oczekiwany przebieg:
- Bardzo szybkie starcie (obie strony speed: 3-4)
- Jazda Tatarska atakuje z dystansu (range: 7)
- Jazda Koronna devastuje w walce wręcz (damage: 20)
- Szybkie załamanie morale jednej ze stron
- **Zwycięzca:** Zazwyczaj Jazda Koronna (wyższe damage i morale)

---

## 🛡️ Scenariusz 3: Piechota vs Kawaleria
**Cel:** Test taktyki defensywnej vs ofensywnej

### Konfiguracja:
```
Armia Koronna:
├── Piechota: 8
└── Dragonia: 2

Kozacy/Tatarzy:
└── Jazda Tatarska: 10
```

### Oczekiwany przebieg:
- Jazda Tatarska krąży i strzela (hit-and-run)
- Piechota Koronna próbuje utrzymać pozycję
- Dragonia zapewnia mobilną obronę
- Wolniejsze tempo bitwy
- **Zwycięzca:** Zazwyczaj Jazda Tatarska (mobilność + zasięg)

---

## 💥 Scenariusz 4: Test Morale
**Cel:** Porównanie determinacji jednostek

### Konfiguracja:
```
Armia Koronna:
└── Pospolite Ruszenie: 15 (morale: 40)

Kozacy/Tatarzy:
└── Piechota Kozacka: 6 (morale: 110)
```

### Oczekiwany przebieg:
- Przewaga liczebna po stronie Koronnej (15 vs 6)
- Pospolite Ruszenie szybko traci morale
- Po 2-3 trafieniach zaczynają uciekać
- Efekt domina - kolejne jednostki panikują
- **Zwycięzca:** Piechota Kozacka (wysokie morale)

---

## 🎖️ Scenariusz 5: Elitarne Oddziały
**Cel:** Najlepsze jednostki każdej strony

### Konfiguracja:
```
Armia Koronna:
├── Piechota: 3 (HP: 120, morale: 100)
├── Dragonia: 3 (speed: 2, range: 6)
└── Jazda: 3 (damage: 20)

Kozacy/Tatarzy:
├── Piechota Kozacka: 5 (morale: 110, damage: 12)
└── Jazda Tatarska: 5 (speed: 4, range: 7)
```

### Oczekiwany przebieg:
- Najciekawsza bitwa - wszystkie typy jednostek
- Różnorodne taktyki po obu stronach
- Długi czas trwania
- Kompleksowa interakcja (zasięg, morale, HP, speed)
- **Zwycięzca:** Zależy od taktyki i losowości

---

## 🏰 Scenariusz 6: Obrona Twierdzy (Symulacja)
**Cel:** Armia Koronna broni, Kozacy atakują

### Konfiguracja:
```
Armia Koronna (Obrońcy):
├── Piechota: 6
└── Dragonia: 2

Kozacy/Tatarzy (Atakujący):
├── Piechota Kozacka: 4
└── Jazda Tatarska: 6
```

### Oczekiwany przebieg:
- Kozacy mają przewagę mobilności
- Armia Koronna stara się utrzymać linię
- Jazda Tatarska flanki
- **Zwycięzca:** Zazwyczaj Kozacy (mobilność + liczebność jazdy)

---

## 🌊 Scenariusz 7: Fala Ataku
**Cel:** Masa jednostek jednego typu

### Konfiguracja:
```
Armia Koronna:
└── Piechota: 20

Kozacy/Tatarzy:
└── Piechota Kozacka: 20
```

### Oczekiwany przebieg:
- Największa bitwa (40 jednostek!)
- Długi czas trwania
- Duże straty po obu stronach
- Test wydajności systemu
- **Zwycięzca:** Piechota Kozacka (wyższe morale i damage)

---

## 🎲 Scenariusz 8: Losowe Szaleństwo
**Cel:** Całkowita nieprzewidywalność

### Konfiguracja:
```
Armia Koronna:
├── Piechota: 2
├── Dragonia: 3
├── Jazda: 1
└── Pospolite Ruszenie: 5

Kozacy/Tatarzy:
├── Piechota Kozacka: 6
└── Jazda Tatarska: 3
```

### Oczekiwany przebieg:
- Chaotyczna bitwa
- Pospolite Ruszenie szybko ucieka
- Pozostałe jednostki walczą zaciekle
- Trudny do przewidzenia wynik
- **Zwycięzca:** ???

---

## 📈 Wskazówki Strategiczne

### Dla Armii Koronnej:
1. **Piechota** - solidna, wytrzymała podstawa armii
2. **Dragonia** - mobilny support, dobry zasięg
3. **Jazda** - śmiertelna w walce wręcz (damage: 20!)
4. **Pospolite Ruszenie** - NIE używaj w małych liczbach (niskie morale)

### Dla Kozaków/Tatarów:
1. **Piechota Kozacka** - najwyższe morale (110), bardzo wytrzymała
2. **Jazda Tatarska** - hit-and-run, najszybsza jednostka (speed: 4)

### Ogólne:
- **Morale > HP** - jednostka z morale < 25 ucieka nawet przy pełnym HP
- **Mobilność = przewaga** - szybsze jednostki kontrolują pole bitwy
- **Zasięg** - możliwość ataku bez odwetu
- **Różnorodność** - mieszanka typów lepiej radzi sobie z różnymi sytuacjami

---

## 🔬 Eksperymenty do Przeprowadzenia

1. **Test morale**: 1 Piechota Kozacka vs 5 Pospolite Ruszenie
2. **Test damage**: 1 Jazda Koronna vs 3 Piechota Kozacka
3. **Test zasięgu**: 5 Jazda Tatarska vs 5 Jazda Koronna
4. **Test speed**: 10 Dragonia vs 10 Piechota
5. **Maximum chaos**: 20x każdego typu (6x20 = 120 jednostek!)

---

Powodzenia w testowaniu! ⚔️🏹🛡️
