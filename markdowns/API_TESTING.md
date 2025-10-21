# 🧪 Testowanie API - Przykładowe Zapytania

Ten plik zawiera przykłady curl/PowerShell do testowania API backendu.

---

## 1️⃣ Sprawdź dostępne typy jednostek

### Curl (Git Bash/Linux):
```bash
curl http://localhost:5000/api/unit-types
```

### PowerShell:
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/unit-types" -Method Get
```

### Oczekiwana odpowiedź:
```json
{
  "Piechota": {
    "faction": "Armia Koronna",
    "hp": 120,
    "morale": 100,
    ...
  },
  ...
}
```

---

## 2️⃣ Rozpocznij symulację

### Curl:
```bash
curl -X POST http://localhost:5000/api/start-simulation \
  -H "Content-Type: application/json" \
  -d '{
    "Piechota": 5,
    "Jazda": 3,
    "Piechota Kozacka": 5,
    "Jazda Tatarska": 5
  }'
```

### PowerShell:
```powershell
$body = @{
    "Piechota" = 5
    "Jazda" = 3
    "Piechota Kozacka" = 5
    "Jazda Tatarska" = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/start-simulation" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

### Oczekiwana odpowiedź:
```json
{
  "status": "started",
  "message": "Symulacja rozpoczęta"
}
```

---

## 3️⃣ Pobierz stan symulacji

### Curl:
```bash
curl http://localhost:5000/api/simulation-step
```

### PowerShell:
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/simulation-step" -Method Get
```

### Oczekiwana odpowiedź:
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
    }
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

---

## 4️⃣ Zatrzymaj symulację

### Curl:
```bash
curl -X POST http://localhost:5000/api/stop-simulation
```

### PowerShell:
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/stop-simulation" -Method Post
```

### Oczekiwana odpowiedź:
```json
{
  "status": "stopped",
  "message": "Symulacja zatrzymana"
}
```

---

## 5️⃣ Pobierz obraz symulacji (alternatywa)

### Curl (zapisz do pliku):
```bash
curl http://localhost:5000/api/simulation-frame -o frame.json
```

### PowerShell:
```powershell
$response = Invoke-RestMethod -Uri "http://localhost:5000/api/simulation-frame" -Method Get
$response.frame  # base64 encoded PNG
```

---

## 🔄 Pełny cykl testowy (PowerShell):

```powershell
# 1. Sprawdź typy jednostek
Write-Host "=== Typy jednostek ===" -ForegroundColor Green
$types = Invoke-RestMethod -Uri "http://localhost:5000/api/unit-types" -Method Get
$types.PSObject.Properties.Name

# 2. Rozpocznij symulację
Write-Host "`n=== Start symulacji ===" -ForegroundColor Green
$config = @{
    "Piechota" = 3
    "Jazda" = 2
    "Piechota Kozacka" = 3
    "Jazda Tatarska" = 2
} | ConvertTo-Json

$start = Invoke-RestMethod -Uri "http://localhost:5000/api/start-simulation" `
  -Method Post -ContentType "application/json" -Body $config
Write-Host $start.message

# 3. Obserwuj przez 10 kroków
Write-Host "`n=== Kroki symulacji ===" -ForegroundColor Green
for ($i = 1; $i -le 10; $i++) {
    Start-Sleep -Milliseconds 500
    $state = Invoke-RestMethod -Uri "http://localhost:5000/api/simulation-step" -Method Get
    Write-Host "Krok $i - Koronna: $($state.stats.crown_count), Kozacy: $($state.stats.cossack_count)"
}

# 4. Zatrzymaj
Write-Host "`n=== Stop ===" -ForegroundColor Green
$stop = Invoke-RestMethod -Uri "http://localhost:5000/api/stop-simulation" -Method Post
Write-Host $stop.message
```

---

## 🔄 Pełny cykl testowy (Bash):

```bash
#!/bin/bash

# 1. Sprawdź typy jednostek
echo "=== Typy jednostek ==="
curl -s http://localhost:5000/api/unit-types | jq 'keys'

# 2. Rozpocznij symulację
echo -e "\n=== Start symulacji ==="
curl -s -X POST http://localhost:5000/api/start-simulation \
  -H "Content-Type: application/json" \
  -d '{
    "Piechota": 3,
    "Jazda": 2,
    "Piechota Kozacka": 3,
    "Jazda Tatarska": 2
  }' | jq '.message'

# 3. Obserwuj przez 10 kroków
echo -e "\n=== Kroki symulacji ==="
for i in {1..10}; do
    sleep 0.5
    STATE=$(curl -s http://localhost:5000/api/simulation-step)
    CROWN=$(echo $STATE | jq '.stats.crown_count')
    COSSACK=$(echo $STATE | jq '.stats.cossack_count')
    echo "Krok $i - Koronna: $CROWN, Kozacy: $COSSACK"
done

# 4. Zatrzymaj
echo -e "\n=== Stop ==="
curl -s -X POST http://localhost:5000/api/stop-simulation | jq '.message'
```

---

## 📊 Przykładowe scenariusze testowe:

### Mała bitwa:
```json
{
  "Piechota": 2,
  "Piechota Kozacka": 2
}
```

### Średnia bitwa:
```json
{
  "Piechota": 5,
  "Dragonia": 2,
  "Jazda": 2,
  "Piechota Kozacka": 5,
  "Jazda Tatarska": 4
}
```

### Duża bitwa:
```json
{
  "Piechota": 10,
  "Dragonia": 5,
  "Jazda": 5,
  "Pospolite Ruszenie": 5,
  "Piechota Kozacka": 12,
  "Jazda Tatarska": 13
}
```

### Test morale:
```json
{
  "Pospolite Ruszenie": 10,
  "Piechota Kozacka": 5
}
```

---

## 🐛 Debugowanie:

### Sprawdź czy serwer działa:
```bash
curl http://localhost:5000/
```

Powinno zwrócić HTML.

### Sprawdź logi serwera:
Patrz w terminal gdzie uruchomiłeś `python app.py`

### Sprawdź błędy JavaScript:
W przeglądarce: F12 → Console

---

Powodzenia w testowaniu! 🧪✨
