let unitTypes = {};
let scenarios = {};
let simulationInterval = null;
let currentScenarioId = null;
let isPaused = false;
let currentScenarioName = null;
let initialUnitsConfig = null;
let canvas = document.getElementById('simulationCanvas');
let ctx = canvas.getContext('2d');

let currentAgents = [];
let tooltip = null;

let spriteCache = {};

let mapData = null;
let tilesetImage = null;

let customUnits = {};
let customErrorTimeout = null;

function showCustomError(message) {
    const toast = document.getElementById('customErrorToast');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('visible');
    if (customErrorTimeout) clearTimeout(customErrorTimeout);
    customErrorTimeout = setTimeout(() => {
        toast.classList.remove('visible');
        customErrorTimeout = null;
    }, 5000);
}

function hideCustomError() {
    const toast = document.getElementById('customErrorToast');
    if (!toast) return;
    toast.classList.remove('visible');
    if (customErrorTimeout) {
        clearTimeout(customErrorTimeout);
        customErrorTimeout = null;
    }
}

function showCustomBattle() {
    document.querySelectorAll('.page-container').forEach(p => p.classList.remove('active'));
    document.getElementById('customBattlePage').classList.add('active');

    const navButtons = document.querySelector('.navigation-buttons');
    if (navButtons) {
        navButtons.style.display = 'none';
    }
    
    hideCustomError();
    
    if (Object.keys(customUnits).length === 0) {
        for (const unit in unitTypes) {
            customUnits[unit] = 0;
        }
    }
    renderCustomControls();
}

function renderCustomControls() {
    const crownContainer = document.getElementById('crownControls');
    const cossackContainer = document.getElementById('cossackControls');
    crownContainer.innerHTML = '';
    cossackContainer.innerHTML = '';
    
    let crownTotal = 0;
    let cossackTotal = 0;

    for (const [name, data] of Object.entries(unitTypes)) {
        const count = customUnits[name] || 0;
        const isCrown = data.faction === 'Armia Koronna';
        
        if (isCrown) crownTotal += count;
        else cossackTotal += count;

        const spriteSrc = data.sprite_path.startsWith('/') ? data.sprite_path : '/' + data.sprite_path;
        const html = `
            <div class="unit-control-row">
                <div class="unit-control-info" style="display: flex; align-items: center; gap: 10px;">
                    <img src="${spriteSrc}" alt="${name}" style="width: 32px; height: 32px; border-radius: 4px; border: 1px solid #555;">
                    <div class="unit-control-name" style="color: ${isCrown ? '#ff6b6b' : '#64b5f6'}">${name}</div>
                </div>
                <div class="unit-control-actions">
                    <button class="btn btn-small" onclick="updateCustomUnit('${name}', -1)">-</button>
                    <span class="count-display">${count}</span>
                    <button class="btn btn-small" onclick="updateCustomUnit('${name}', 1)">+</button>
                </div>
            </div>
        `;
        
        if (isCrown) crownContainer.innerHTML += html;
        else cossackContainer.innerHTML += html;
    }
    
    document.getElementById('crownTotalDisplay').innerText = crownTotal;
    document.getElementById('cossackTotalDisplay').innerText = cossackTotal;
}

function updateCustomUnit(name, delta) {
    if (!customUnits[name]) customUnits[name] = 0;
    customUnits[name] += delta;
    if (customUnits[name] < 0) customUnits[name] = 0;
    if (customUnits[name] > 20) customUnits[name] = 20; // Limit per unit type
    hideCustomError();
    renderCustomControls();
}

function startCustomSimulation() {
    const config = {};
    let crownTotal = 0;
    let cossackTotal = 0;
    for (const [name, count] of Object.entries(customUnits)) {
        if (count > 0) {
            config[name] = count;
            const faction = unitTypes[name]?.faction;
            if (faction === 'Armia Koronna') {
                crownTotal += count;
            } else if (faction === 'Kozacy/Tatarzy') {
                cossackTotal += count;
            }
        }
    }
    
    if (Object.keys(config).length === 0) {
        showCustomError("Dodaj jednostki, aby rozpocząć bitwę.");
        return;
    }

    if (crownTotal === 0 || cossackTotal === 0) {
        showCustomError("Każda armia musi mieć co najmniej 1 jednostkę.");
        return;
    }

    hideCustomError();
    
    const weatherSelect = document.getElementById('customWeatherSelect');
    const weather = weatherSelect ? weatherSelect.value : 'clear';

    fetch('/api/start-simulation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            units_config: config,
            scenario_id: 'custom',
            weather: weather
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'started') {
            currentScenarioId = 'custom';
            currentScenarioName = "Własna Bitwa";
            initialUnitsConfig = config;
            
            setWeather(weather);

            document.querySelector('.main-grid').classList.add('simulation-active');
            document.querySelectorAll('.page-container').forEach(p => p.classList.remove('active'));
            document.querySelector('.navigation-buttons').style.display = 'none';
            document.getElementById('simulationArea').style.display = 'block';
            document.getElementById('controlPanel').style.display = 'block';
            document.getElementById('battleStats').style.display = 'block';
            
            if (simulationInterval) clearInterval(simulationInterval);
            simulationInterval = setInterval(updateSimulation, 200);
            
            updateStatus('Symulacja w toku', 'running');
        }
    })
    .catch(error => console.error('Error starting custom simulation:', error));
}

function loadSprite(spritePath) {
    return new Promise((resolve, reject) => {
        if (spriteCache[spritePath]) {
            resolve(spriteCache[spritePath]);
            return;
        }
        
        const img = new Image();
        img.onload = () => {
            spriteCache[spritePath] = img;
            resolve(img);
        };
        img.onerror = (e) => {
            console.error(`Failed to load sprite: ${spritePath}`, e);
            resolve(null);
        };
        const fullPath = spritePath.startsWith('/') ? spritePath : '/' + spritePath;
        img.src = fullPath;
    });
}

async function preloadSprites() {
    const promises = Object.values(unitTypes).map(unit => loadSprite(unit.sprite_path));
    await Promise.all(promises);
    console.log('Sprites preloaded:', Object.keys(spriteCache).length);
}

async function loadMapData() {
    try {
        const response = await fetch('/api/map-data');
        mapData = await response.json();
        
        if (mapData.error) {
            console.error("Backend error:", mapData.error);
            return;
        }

        console.log('Map data loaded:', mapData.width, 'x', mapData.height);
        console.log('Tileset config: columns=', mapData.tileset_columns, 'spacing=', mapData.tileset_spacing, 'firstgid=', mapData.tileset_firstgid);
        console.log('First row of tiles (first 10):', mapData.tiles[0].slice(0, 10));
        console.log('Unique GIDs in first row:', [...new Set(mapData.tiles[0])]);
        
        if (!mapData.tileset_image) {
            console.error("Missing tileset_image in mapData!");
            return;
        }

        tilesetImage = new Image();
        tilesetImage.onload = () => {
            console.log('Tileset image loaded successfully');
        };
        tilesetImage.onerror = (e) => {
            console.error('Failed to load tileset image:', mapData.tileset_image, e);
        };
        
        const tilesetPath = mapData.tileset_image.startsWith('/') ? mapData.tileset_image : '/' + mapData.tileset_image;
        tilesetImage.src = tilesetPath;
    } catch (error) {
        console.error('CRITICAL: Błąd ładowania mapy:', error);
    }
}

async function loadUnitTypes() {
    try {
        const response = await fetch('/api/unit-types');
        unitTypes = await response.json();
        
        renderLegend();
        
        await preloadSprites();
        await loadMapData();
    } catch (error) {
        console.error('Błąd ładowania typów jednostek:', error);
    }
}

async function loadScenarios() {
    try {
        const response = await fetch('/api/scenarios');
        scenarios = await response.json();
        renderScenarios();
    } catch (error) {
        console.error('Błąd ładowania scenariuszy:', error);
    }
}

function renderScenarios() {
    const grid = document.getElementById('scenariosGrid');
    grid.innerHTML = '';
    console.log(scenarios);

    let armyCoronaUnits = [
        "Husaria", "Pancerni", "Rajtaria", "Dragonia", 
        "Piechota Niemiecka", "Pospolite Ruszenie", 
        "Czeladz Obozowa", "Artyleria Koronna"
    ];
    let armyCossackUnits = [
        "Jazda Tatarska", "Piechota Kozacka", "Czern", 
        "Jazda Kozacka", "Artyleria Kozacka"
    ];

    for (const [scenarioId, scenario] of Object.entries(scenarios)) {
        const card = document.createElement('div');
        card.className = 'scenario-card';
        card.onclick = () => selectScenario(scenarioId);
        
        const crownUnits = [];
        const cossackUnits = [];
        let totalCrown = 0;
        let totalCossack = 0;
        
        for (const [unitName, count] of Object.entries(scenario.units)) {
            if (unitName.startsWith('_')) continue;
            
            if (count > 0) {
                if (armyCoronaUnits.includes(unitName)) {
                    crownUnits.push({ name: unitName, count });
                    totalCrown += count;
                } else {
                    cossackUnits.push({ name: unitName, count });
                    totalCossack += count;
                }
            }
        }
        
        let unitsHTML = '';
        
        if (crownUnits.length > 0) {
            unitsHTML += '<div class="scenario-faction-header">Armia Koronna</div>';
            crownUnits.forEach(unit => {
                unitsHTML += `
                    <div class="scenario-unit-row">
                        <span class="scenario-unit-name">${unit.name}</span>
                        <span class="scenario-unit-count">${unit.count}</span>
                    </div>
                `;
            });
        }
        
        if (cossackUnits.length > 0) {
            unitsHTML += '<div class="scenario-faction-header">Kozacy/Tatarzy</div>';
            cossackUnits.forEach(unit => {
                unitsHTML += `
                    <div class="scenario-unit-row">
                        <span class="scenario-unit-name">${unit.name}</span>
                        <span class="scenario-unit-count">${unit.count}</span>
                    </div>
                `;
            });
        }
        
        const totalUnits = totalCrown + totalCossack;
        
        let forcesSummary = '';
        if (totalCrown > 0 || totalCossack > 0) {
            forcesSummary = `
                <div class="scenario-forces-summary">
                    <div class="scenario-force-row">
                        <span class="scenario-force-label crown-color">Armia Koronna:</span>
                        <span class="scenario-force-value crown-color">${totalCrown}</span>
                    </div>
                    <div class="scenario-force-row">
                        <span class="scenario-force-label cossack-color">Kozacy/Tatarzy:</span>
                        <span class="scenario-force-value cossack-color">${totalCossack}</span>
                    </div>
                </div>
            `;
        }
        
        card.innerHTML = `
            <div class="scenario-title">${scenario.name}</div>
            <div class="scenario-description">${scenario.description}</div>
            <div class="scenario-units">
                ${unitsHTML}
            </div>
            ${forcesSummary}
            <div class="scenario-total">
                <span>Łącznie jednostek:</span>
                <span>${totalUnits}</span>
            </div>
        `;
        
        grid.appendChild(card);
    }
}

async function selectScenario(scenarioId) {
    const scenario = scenarios[scenarioId];
    if (!scenario) return;
    
    const weatherSelect = document.getElementById('scenarioWeatherSelect');
    const weather = weatherSelect ? weatherSelect.value : 'clear';
    
    console.log('Wybrano scenariusz:', scenario.name, 'Pogoda:', weather);
    
    currentScenarioId = scenarioId;
    currentScenarioName = scenario.name;
    initialUnitsConfig = {...scenario.units};
    
    document.getElementById('loader').classList.add('active');
    
    try {
        const response = await fetch('/api/start-simulation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                units_config: scenario.units,
                scenario_id: scenarioId,
                weather: weather
            })
        });
        
        const result = await response.json();
        console.log('Start result:', result);
        
        if (response.ok) {
            setWeather(weather);

            document.querySelector('.main-grid').classList.add('simulation-active');
            document.getElementById('scenariosPage').style.display = 'none';
            document.querySelector('.navigation-buttons').style.display = 'none';
            document.getElementById('controlPanel').style.display = 'block';
            document.getElementById('simulationArea').style.display = 'block';
            
            updateStatus('running', 'Symulacja w toku');
            document.getElementById('battleStats').style.display = 'block';
            
            simulationInterval = setInterval(updateSimulation, 200);
            console.log('Simulation interval started');
        }
    } catch (error) {
        console.error('Błąd rozpoczynania symulacji:', error);
        alert('Nie udało się rozpocząć symulacji');
    } finally {
        document.getElementById('loader').classList.remove('active');
    }
}

async function backToScenarios() {
    if (simulationInterval) {
        clearInterval(simulationInterval);
        simulationInterval = null;
    }
    
    isPaused = false;
    
    await clearSimulation();
    
    document.querySelector('.main-grid').classList.remove('simulation-active');
    document.querySelector('.navigation-buttons').style.display = '';
    document.getElementById('scenariosPage').style.display = '';
    showPage('scenarios');
    document.getElementById('controlPanel').style.display = 'none';
    document.getElementById('simulationArea').style.display = 'none';
    document.getElementById('battleStats').style.display = 'none';
    
    const pauseBtn = document.getElementById('pauseBtn');
    if (pauseBtn) {
        pauseBtn.textContent = '⏸️ Pauza';
        pauseBtn.classList.remove('btn-start');
        pauseBtn.classList.add('btn-stop');
    }
    
    if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    
    updateStatus('idle', 'Gotowa do startu');
}

async function clearSimulation() {
    try {
        await fetch('/api/stop-simulation', { method: 'POST' });
        
        if (simulationInterval) {
            clearInterval(simulationInterval);
            simulationInterval = null;
        }
        
        console.log('Symulacja wyczyszczona');
    } catch (error) {
        console.error('Błąd czyszczenia symulacji:', error);
    }
}


function renderLegend() {
    const crownContainer = document.getElementById('crownLegendContainer');
    const cossackContainer = document.getElementById('cossackLegendContainer');
    
    crownContainer.innerHTML = '';
    cossackContainer.innerHTML = '';
    
    for (const [unitName, unitData] of Object.entries(unitTypes)) {
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        
        const factionClass = unitData.faction === 'Armia Koronna' ? 'crown-color' : 'cossack-color';
        
        legendItem.innerHTML = `
            <img src="/${unitData.sprite_path}" alt="${unitName}" class="legend-icon" 
                    onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2240%22 height=%2240%22><rect width=%2240%22 height=%2240%22 fill=%22%23666%22/></svg>'">
            <div class="legend-info">
                <div class="legend-name">${unitName}</div>
                <div class="legend-faction ${factionClass}">${unitData.description || unitData.faction}</div>
                <div class="legend-stats">
                    <div class="stat">
                        <span class="stat-label">HP:</span>
                        <span class="stat-value">${unitData.hp}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Morale:</span>
                        <span class="stat-value">${unitData.morale}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Zasięg:</span>
                        <span class="stat-value">${unitData.range}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Atak:</span>
                        <span class="stat-value">${unitData.damage}</span>
                    </div>
                </div>
            </div>
        `;
        
        if (unitData.faction === 'Armia Koronna') {
            crownContainer.appendChild(legendItem);
        } else {
            cossackContainer.appendChild(legendItem);
        }
    }
}

function showPage(pageName) {
    document.querySelectorAll('.page-container').forEach(page => {
        page.classList.remove('active');
    });
    
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    if (pageName === 'scenarios') {
        document.getElementById('scenariosPage').classList.add('active');
        document.getElementById('navScenarios').classList.add('active');
    } else if (pageName === 'legend') {
        document.getElementById('legendPage').classList.add('active');
        document.getElementById('navLegend').classList.add('active');
    }
}


function togglePause() {
    isPaused = !isPaused;
    const pauseBtn = document.getElementById('pauseBtn');
    
    if (isPaused) {
        pauseBtn.textContent = '▶️ Wznów';
        pauseBtn.classList.remove('btn-stop');
        pauseBtn.classList.add('btn-start');
        updateStatus('paused', 'Symulacja wstrzymana');
    } else {
        pauseBtn.textContent = '⏸️ Pauza';
        pauseBtn.classList.remove('btn-start');
        pauseBtn.classList.add('btn-stop');
        updateStatus('running', 'Symulacja w toku');
    }
}

async function stopSimulation() {
    try {
        await fetch('/api/stop-simulation', { method: 'POST' });
        backToScenarios();
    } catch (error) {
        console.error('Błąd zatrzymywania symulacji:', error);
    }
}

async function updateSimulation() {
    try {
        if (isPaused) {
            return;
        }
        
        if (!simulationInterval) {
            return;
        }
        
        const response = await fetch('/api/simulation-step');
        
        if (!response.ok) {
            console.warn('Simulation step failed:', response.status);
            if (response.status === 400) {
                if (simulationInterval) {
                    clearInterval(simulationInterval);
                    simulationInterval = null;
                }
            }
            return;
        }
        
        const data = await response.json();
        
        if (data.error) {
            console.warn('Simulation error:', data.error);
            return;
        }
        
        if (!data || !data.stats) {
            console.warn('Invalid simulation data received');
            return;
        }
        
        console.log('Simulation step:', data.stats);
        
        renderSimulation(data);
        
        document.getElementById('crownCount').textContent = data.stats.crown_count;
        document.getElementById('cossackCount').textContent = data.stats.cossack_count;
        document.getElementById('totalCount').textContent = data.stats.total_agents;
        
        if (data.battle_status && data.battle_status.status === 'finished') {
            if (simulationInterval) {
                clearInterval(simulationInterval);
                simulationInterval = null;
            }
            data.battle_status.crown_count = data.stats.crown_count;
            data.battle_status.cossack_count = data.stats.cossack_count;
            data.battle_status.total_agents = data.stats.total_agents;
            showVictoryModal(data.battle_status);
        }
    } catch (error) {
        console.error('Błąd aktualizacji symulacji:', error);
    }
}

async function showVictoryModal(battleStatus) {
    const modal = document.getElementById('victoryModal');
    const winnerEl = document.getElementById('victoryWinner');
    const statsEl = document.getElementById('victoryStats');
    
    let winnerClass = '';
    let emoji = '';
    let winnerText = '';
    
    if (battleStatus.winner === 'Armia Koronna') {
        winnerClass = 'victory-crown';
        winnerText = 'ARMIA KORONNA ZWYCIĘŻA';
    } else if (battleStatus.winner === 'Kozacy/Tatarzy') {
        winnerClass = 'victory-cossack';
        winnerText = 'KOZACY I TATARZY ZWYCIĘŻAJĄ';
    } else {
        winnerClass = 'victory-draw';
        winnerText = 'REMIS - OBIE STRONY WYCZERPANE';
    }
    
    winnerEl.className = `victory-winner ${winnerClass}`;
    winnerEl.textContent = winnerText;
    
    if (battleStatus.winner !== 'Remis') {
        statsEl.innerHTML = `
            <div>Pozostało jednostek: <strong>${battleStatus.survivors}</strong></div>
            
        `;
    } else {
        statsEl.innerHTML = `
            <div>Obie armie poniosły ciężkie straty</div>
            <div>Nikt nie wyszedł zwycięsko z tej bitwy</div>
        `;
    }
    
    await saveBattleResult(battleStatus);
    
    modal.classList.add('active');
    updateStatus('stopped', 'Bitwa zakończona');
}

async function saveBattleResult(battleStatus) {
    try {
        const crownCount = parseInt(document.getElementById('crownCount').textContent) || 0;
        const cossackCount = parseInt(document.getElementById('cossackCount').textContent) || 0;
        const totalCount = parseInt(document.getElementById('totalCount').textContent) || 0;
        
        const resultData = {
            scenario_id: currentScenarioId,
            scenario_name: currentScenarioName || 'Unknown',
            winner: battleStatus.winner || 'Remis',
            survivors: battleStatus.survivors || 0,
            crown_count: crownCount,
            cossack_count: cossackCount,
            total_agents: totalCount,
            initial_units: initialUnitsConfig || {}
        };
        
        const response = await fetch('/api/save-battle-result', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(resultData)
        });
        
        if (response.ok) {
            console.log('Wynik bitwy zapisany:', resultData);
        } else {
            console.error('Błąd zapisywania wyniku bitwy');
        }
    } catch (error) {
        console.error('Błąd zapisywania wyniku bitwy:', error);
    }
}

function closeVictoryModal() {
    const modal = document.getElementById('victoryModal');
    modal.classList.remove('active');
}

function restartSimulation() {
    closeVictoryModal();
    backToScenarios();
}

let currentWeather = 'clear';
let weatherNeedsInit = false;
let rainParticles = [];
let fogParticles = [];

function initRain(width, height) {
    rainParticles = [];
    const density = 1000;
    const count = Math.floor((width * height) / density);
    
    console.log(`Inicjalizacja deszczu: ${count} kropel dla obszaru ${width}x${height}`);
    
    for (let i = 0; i < count; i++) {
        rainParticles.push({
            x: Math.random() * width,
            y: Math.random() * height,
            speed: Math.random() * 15 + 10,
            length: Math.random() * 15 + 10
        });
    }
}

function initFog(width, height) {
    fogParticles = [];
    const count = 20;
    
    console.log(`Inicjalizacja mgły: ${count} dużych chmur dla obszaru ${width}x${height}`);

    for (let i = 0; i < count; i++) {
        fogParticles.push({
            x: Math.random() * width,
            y: Math.random() * height,
            vx: (Math.random() - 0.5) * 0.2,
            vy: (Math.random() - 0.5) * 0.2,
            radius: Math.random() * 200 + 100,
            alpha: Math.random() * 0.1 + 0.05
        });
    }
}

function drawRain(ctx, width, height) {
    if (rainParticles.length === 0) return;

    ctx.strokeStyle = 'rgba(200, 220, 255, 0.8)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    for (let p of rainParticles) {
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(p.x, p.y + p.length);
        
        p.y += p.speed;
        
        if (p.y > height) {
            p.y = -p.length;
            p.x = Math.random() * width;
        }
    }
    ctx.stroke();
}

function drawFog(ctx, width, height) {
    ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.fillRect(0, 0, width, height);

    for (let p of fogParticles) {
        ctx.beginPath();
        const gradient = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.radius);
        gradient.addColorStop(0, `rgba(255, 255, 255, ${p.alpha})`);
        gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
        
        ctx.fillStyle = gradient;
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();
        
        p.x += p.vx;
        p.y += p.vy;
        
        if (p.x < -p.radius) p.x = width + p.radius;
        if (p.x > width + p.radius) p.x = -p.radius;
        if (p.y < -p.radius) p.y = height + p.radius;
        if (p.y > height + p.radius) p.y = -p.radius;
    }
}

window.setWeather = function(type) {
    currentWeather = type;
    weatherNeedsInit = true;
};

function renderSimulation(data) {
    const tileSize = 16;
    const scale = 2;
    
    currentAgents = data.agents || [];

    canvas.width = data.map_width * tileSize * scale;
    canvas.height = data.map_height * tileSize * scale;

    if (weatherNeedsInit || (currentWeather === 'rain' && rainParticles.length === 0) || (currentWeather === 'fog' && fogParticles.length === 0)) {
        if (currentWeather === 'rain') initRain(canvas.width, canvas.height);
        else if (currentWeather === 'fog') initFog(canvas.width, canvas.height);
        else { rainParticles = []; fogParticles = []; }
        weatherNeedsInit = false;
    }
    
    ctx.fillStyle = '#2d5016';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    console.log('Rendering map - mapData:', !!mapData, 'tilesetImage:', !!tilesetImage, 'complete:', tilesetImage?.complete, 'src:', tilesetImage?.src);
    
    if (mapData && tilesetImage && tilesetImage.complete) {
        const tilesPerRow = mapData.tileset_columns || 32;
        const spacing = mapData.tileset_spacing || 0;
        const firstgid = mapData.tileset_firstgid || 1;
        
        let tilesDrawn = 0;
        let debugLog = false;
        
        for (let y = 0; y < mapData.height; y++) {
            const row = mapData.tiles[y];
            const flagsRow = mapData.flip_flags ? mapData.flip_flags[y] : null;
            
            if (!row || !Array.isArray(row)) {
                console.error(`Row ${y} is not an array:`, row);
                continue;
            }
            
            for (let x = 0; x < mapData.width; x++) {
                const gid = row[x];
                if (gid === 0 || gid === undefined || gid === null) continue;
                
                const tileId = gid - firstgid;
                if (tileId < 0) continue;
                
                const col = tileId % tilesPerRow;
                const tilesetRow = Math.floor(tileId / tilesPerRow);
                
                const srcX = col * (mapData.tile_width + spacing);
                const srcY = tilesetRow * (mapData.tile_height + spacing);
                
                const destX = x * tileSize * scale;
                const destY = y * tileSize * scale;
                
                const flags = flagsRow ? flagsRow[x] : {h: false, v: false, d: false};
                
                ctx.save();
                
                if (flags.h || flags.v || flags.d) {
                    ctx.translate(destX + (tileSize * scale) / 2, destY + (tileSize * scale) / 2);
                    
                    if (flags.d) {
                        ctx.rotate(Math.PI / 2);
                        ctx.scale(-1, 1);
                    }
                    if (flags.h) {
                        ctx.scale(-1, 1);
                    }
                    if (flags.v) {
                        ctx.scale(1, -1);
                    }
                    
                    ctx.drawImage(
                        tilesetImage,
                        srcX, srcY, mapData.tile_width, mapData.tile_height,
                        -(tileSize * scale) / 2, -(tileSize * scale) / 2, 
                        tileSize * scale, tileSize * scale
                    );
                } else {
                    ctx.drawImage(
                        tilesetImage,
                        srcX, srcY, mapData.tile_width, mapData.tile_height,
                        destX, destY, tileSize * scale, tileSize * scale
                    );
                }
                
                ctx.restore();
                tilesDrawn++;
            }
        }
        
        if (tilesDrawn === 0) {
            console.warn('No tiles drawn! Check mapData.tiles structure');
        }
    } else {
        ctx.strokeStyle = 'rgba(0, 0, 0, 0.1)';
        ctx.lineWidth = 0.5;
        for (let x = 0; x < canvas.width; x += tileSize * scale) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        }
        for (let y = 0; y < canvas.height; y += tileSize * scale) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }
    }
    
    ctx.strokeStyle = 'rgba(50, 50, 200, 0.5)';
    ctx.lineWidth = 3;
    const cossackZoneY = 15 * tileSize * scale;
    ctx.strokeRect(0, 0, canvas.width, cossackZoneY);
    
    ctx.strokeStyle = 'rgba(200, 50, 50, 0.5)';
    const crownZoneY = (data.map_height - 15) * tileSize * scale;
    ctx.strokeRect(0, crownZoneY, canvas.width, canvas.height - crownZoneY);
    
    if (data.agents && Array.isArray(data.agents)) {
        data.agents.forEach(agent => {
        const x = (agent.x + 0.5) * tileSize * scale;
        const y = (agent.y + 0.5) * tileSize * scale;
        
        const sprite = spriteCache[agent.sprite_path];
        if (sprite) {
            const spriteSize = tileSize * scale * 2.5;
            ctx.drawImage(sprite, 
                x - spriteSize / 2, 
                y - spriteSize / 2, 
                spriteSize, 
                spriteSize
            );
        } else {
            const baseColor = agent.faction === 'Armia Koronna' ? '#d4a5a5' : '#a5b4d4';
            const size = 8 * scale;
            
            ctx.fillStyle = baseColor;
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            
            if (agent.unit_type.includes('Piechota')) {
                ctx.fillRect(x - size, y - size, size * 2, size * 2);
                ctx.strokeRect(x - size, y - size, size * 2, size * 2);
            } else if (agent.unit_type.includes('Jazda') || agent.unit_type.includes('Cavalry')) {
                ctx.beginPath();
                ctx.moveTo(x, y - size * 1.5);
                ctx.lineTo(x - size * 1.3, y + size);
                ctx.lineTo(x + size * 1.3, y + size);
                ctx.closePath();
                ctx.fill();
                ctx.stroke();
            } else if (agent.unit_type.includes('Dragonia')) {
                ctx.beginPath();
                ctx.moveTo(x, y - size * 1.5);
                ctx.lineTo(x + size, y);
                ctx.lineTo(x, y + size * 1.5);
                ctx.lineTo(x - size, y);
                ctx.closePath();
                ctx.fill();
                ctx.stroke();
            } else {
                ctx.beginPath();
                ctx.arc(x, y, size, 0, Math.PI * 2);
                ctx.fill();
                ctx.stroke();
            }
        }
        
        const barWidth = 28 * scale;
        const barHeight = 5 * scale;
        
        const hpY = y - 16 * scale;
        const hpPercent = agent.hp / agent.max_hp;
        
        ctx.fillStyle = '#c00';
        ctx.fillRect(x - barWidth/2, hpY - barHeight/2, barWidth, barHeight);
        
        if (hpPercent > 0) {
            ctx.fillStyle = '#0c0';
            ctx.fillRect(x - barWidth/2, hpY - barHeight/2, barWidth * hpPercent, barHeight);
        }
        
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 1;
        ctx.strokeRect(x - barWidth/2, hpY - barHeight/2, barWidth, barHeight);
        
        const moraleY = y - 24 * scale;
        const moralePercent = agent.morale / agent.max_morale;
        
        ctx.fillStyle = '#666';
        ctx.fillRect(x - barWidth/2, moraleY - barHeight/2, barWidth, barHeight);
        
        if (moralePercent > 0) {
            ctx.fillStyle = '#0cc';
            ctx.fillRect(x - barWidth/2, moraleY - barHeight/2, barWidth * moralePercent, barHeight);
        }
        
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 1;
        ctx.strokeRect(x - barWidth/2, moraleY - barHeight/2, barWidth, barHeight);
    });
    }

    const healingZones = data.healing_zones || [
        {x: 115, y: 15}, {x: 135, y: 15},
        {x: 115, y: 50}, {x: 135, y: 50},
        {x: 115, y: 85}, {x: 135, y: 85}
    ];

    ctx.lineWidth = 2;

    healingZones.forEach(zone => {
        if (zone.x >= data.map_width || zone.y >= data.map_height) {
            console.warn('Healing zone out of bounds:', zone);
            return;
        }

        const zx = zone.x * tileSize * scale;
        const zy = zone.y * tileSize * scale;
        const size = tileSize * scale;

        ctx.fillStyle = 'rgba(0, 255, 0, 0.4)';
        ctx.strokeStyle = 'rgba(0, 255, 0, 0.9)';
        
        ctx.fillRect(zx, zy, size, size);
        ctx.strokeRect(zx, zy, size, size);

        ctx.save();
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(255, 255, 255, 1.0)';
        ctx.lineWidth = 3;
        
        const crossSize = size * 0.6;
        const offset = (size - crossSize) / 2;

        ctx.moveTo(zx + size/2, zy + offset);
        ctx.lineTo(zx + size/2, zy + size - offset);
        
        ctx.moveTo(zx + offset, zy + size/2);
        ctx.lineTo(zx + size - offset, zy + size/2);
        
        ctx.stroke();
        ctx.restore();
    });

    if (currentWeather === 'rain') {
        drawRain(ctx, canvas.width, canvas.height);
    } else if (currentWeather === 'fog') {
        drawFog(ctx, canvas.width, canvas.height);
    }
}

function updateStatus(status, text) {
    const statusEl = document.getElementById('status');
    statusEl.className = `simulation-status status-${status}`;
    statusEl.textContent = text;
}

loadUnitTypes();
loadScenarios();

function setupTooltip() {
    tooltip = document.createElement('div');
    tooltip.id = 'agent-tooltip';
    tooltip.style.position = 'absolute';
    tooltip.style.display = 'none';
    tooltip.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
    tooltip.style.color = 'white';
    tooltip.style.padding = '10px';
    tooltip.style.borderRadius = '6px';
    tooltip.style.fontSize = '13px';
    tooltip.style.pointerEvents = 'none';
    tooltip.style.zIndex = '10000';
    tooltip.style.whiteSpace = 'pre-line';
    tooltip.style.border = '1px solid #555';
    tooltip.style.boxShadow = '0 4px 8px rgba(0,0,0,0.5)';
    tooltip.style.minWidth = '150px';
    document.body.appendChild(tooltip);

    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseout', () => {
        if (tooltip) tooltip.style.display = 'none';
    });
}

function handleMouseMove(e) {
    if (!currentAgents || currentAgents.length === 0) return;
    if (!tooltip) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const mouseX = (e.clientX - rect.left) * scaleX;
    const mouseY = (e.clientY - rect.top) * scaleY;

    const tileSize = 16;
    const scale = 2;
    const spriteSize = tileSize * scale * 2.5;

    let found = false;
    
    for (let i = currentAgents.length - 1; i >= 0; i--) {
        const agent = currentAgents[i];
        const x = (agent.x + 0.5) * tileSize * scale;
        const y = (agent.y + 0.5) * tileSize * scale;
        
        if (mouseX >= x - spriteSize / 2 && mouseX <= x + spriteSize / 2 &&
            mouseY >= y - spriteSize / 2 && mouseY <= y + spriteSize / 2) {
            
            showTooltip(e.clientX, e.clientY, agent);
            found = true;
            break;
        }
    }

    if (!found) {
        tooltip.style.display = 'none';
    }
}

function showTooltip(screenX, screenY, agent) {
    tooltip.style.display = 'block';
    
    let left = screenX + 15;
    let top = screenY + 15;
    
    if (left + 200 > window.innerWidth) left = screenX - 215;
    if (top + 150 > window.innerHeight) top = screenY - 165;

    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
    
    const factionColor = agent.faction === 'Armia Koronna' ? '#ff6b6b' : '#64b5f6';
    const stateMap = {
        'IDLE': 'Bezczynny',
        'MOVING': 'Ruch',
        'ATTACKING': 'Walka',
        'FLEEING': 'Ucieczka',
        'MOVING_TO_STRATEGIC': 'Ruch Strategiczny'
    };
    const stateText = stateMap[agent.state] || agent.state;
    
    let healingStatus = '';
    if (agent.faction === 'Armia Koronna') {
        const healingZones = [
            {x: 115, y: 15}, {x: 135, y: 15},
            {x: 115, y: 50}, {x: 135, y: 50},
            {x: 115, y: 85}, {x: 135, y: 85}
        ];
        
        const isHealing = healingZones.some(z => Math.abs(agent.x - z.x) < 1.5 && Math.abs(agent.y - z.y) < 1.5);
        
        if (isHealing && agent.hp < agent.max_hp) {
            healingStatus = '<div style="color: #4caf50; font-weight: bold; margin-top: 5px; text-align: center;">🏥 LECZENIE (+5 HP/tura)</div>';
        }
    }

    tooltip.innerHTML = `
        <div style="border-bottom: 1px solid #555; padding-bottom: 5px; margin-bottom: 5px;">
            <strong style="color: ${factionColor}; font-size: 1.1em;">${agent.unit_type}</strong>
            <div style="font-size: 0.85em; color: #aaa;">${agent.faction}</div>
        </div>
        <div style="display: grid; grid-template-columns: auto auto; gap: 5px 15px;">
            <span style="color: #ccc;">HP:</span> 
            <span style="color: ${getHpColor(agent.hp, agent.max_hp)}">${Math.round(agent.hp)}/${agent.max_hp}</span>
            
            <span style="color: #ccc;">Morale:</span>
            <span style="color: #0cc">${Math.round(agent.morale)}/${agent.max_morale}</span>
            
            <span style="color: #ccc;">Stan:</span>
            <span style="color: #fff">${stateText}</span>
        </div>
        ${healingStatus}
    `;
}

function getHpColor(current, max) {
    const pct = current / max;
    if (pct > 0.6) return '#4caf50';
    if (pct > 0.3) return '#ff9800';
    return '#f44336';
}

setupTooltip();
