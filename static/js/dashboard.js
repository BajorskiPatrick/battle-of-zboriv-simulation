let rawData = [];
let filtered = [];
let currentTimeFilter = 'all';
let chartMeta = [];
let chartTooltipEl = null;
let chartCanvas = null;

document.addEventListener('DOMContentLoaded', () => {
  const refreshBtn = document.getElementById('refreshBtn');
  const scenarioFilter = document.getElementById('scenarioFilter');
  chartTooltipEl = document.getElementById('chartTooltip');

  refreshBtn.addEventListener('click', loadData);
  scenarioFilter.addEventListener('change', applyFilters);

  const resetBtn = document.getElementById('resetBtn');
  if (resetBtn) {
      resetBtn.addEventListener('click', clearData);
  }

  document.querySelectorAll('[data-time-filter]').forEach(btn => {
    btn.addEventListener('click', () => setTimeFilter(btn));
  });

  loadData();
});

async function clearData() {
    if (!confirm("Czy na pewno chcesz usunąć wszystkie wyniki bitew? Tej operacji nie można cofnąć.")) {
        return;
    }
    try {
        const res = await fetch('/api/clear-battle-results', { method: 'POST' });
        const json = await res.json();
        if (json.ok) {
            loadData();
        } else {
            alert("Błąd podczas usuwania danych: " + json.error);
        }
    } catch (e) {
        console.error('Error clearing results:', e);
        alert("Błąd połączenia z serwerem.");
    }
}

async function loadData() {
  try {
    const res = await fetch('/api/battle-results');
    const json = await res.json();
    if (!json.ok) return;
    rawData = json.data || [];
    populateScenarioFilter(rawData);
    applyFilters();
  } catch (e) {
    console.error('Error loading results:', e);
  }
}

function populateScenarioFilter(data) {
  const select = document.getElementById('scenarioFilter');
  const names = Array.from(new Set(data.map(r => r.scenario_name))).filter(Boolean).sort();
  select.querySelectorAll('option:not([value="__ALL__"])').forEach(o => o.remove());
  names.forEach(n => {
    const opt = document.createElement('option');
    opt.value = n; opt.textContent = n;
    select.appendChild(opt);
  });
}

function applyFilters() {
  const scenario = document.getElementById('scenarioFilter').value;
  const time = currentTimeFilter;
  const now = Date.now();

  filtered = rawData.filter(r => {
    const okScenario = (scenario === '__ALL__' || r.scenario_name === scenario);
    let okTime = true;
    if (time !== 'all') {
      const ts = new Date((r.timestamp || '').replace(' ', 'T')).getTime();
      const delta = now - ts;
      okTime = (time === '24h') ? delta <= 24*3600*1000 : delta <= 7*24*3600*1000;
    }
    return okScenario && okTime;
  });

  renderWinsChartAnimated(filtered);
  renderResultsTable(filtered);
}

function groupBy(arr, key) {
  return arr.reduce((acc, item) => {
    const k = item[key] || 'Unknown';
    (acc[k] = acc[k] || []).push(item);
    return acc;
  }, {});
}

function setTimeFilter(button) {
  if (!button) return;
  const value = button.dataset.timeFilter;
  if (!value) return;
  currentTimeFilter = value;
  document.querySelectorAll('[data-time-filter]').forEach(btn => {
    btn.classList.toggle('active', btn === button);
  });
  applyFilters();
}

function renderWinsChartAnimated(data) {
  const byScenario = groupBy(data, 'scenario_name');
  const labels = Object.keys(byScenario);
  const crown = labels.map(s => byScenario[s].filter(r => r.winner === 'Armia Koronna').length);
  const cossack = labels.map(s => byScenario[s].filter(r => r.winner === 'Kozacy/Tatarzy').length);
  const draw = labels.map(s => byScenario[s].filter(r => r.winner === 'Remis').length);

  const canvas = document.getElementById('winsChartAnimated');
  if (!canvas) return;
  chartCanvas = canvas;
  const ctx = canvas.getContext('2d');
  canvas.width = canvas.clientWidth || 1400; canvas.height = 420;
  ctx.clearRect(0,0,canvas.width,canvas.height);

  const max = Math.max(1, ...labels.map((_, i) => crown[i]+cossack[i]+draw[i]));
  const barW = Math.max(24, Math.floor((canvas.width - 120) / Math.max(1, labels.length)));
  const baseY = canvas.height - 50;

  const avgSurvivors = data.length ? (data.reduce((s, r) => s + (r.survivors||0), 0) / data.length) : 0;
  const statEl = document.getElementById('avgSurvivorsStat');
  if (statEl) statEl.textContent = avgSurvivors.toFixed(1);
  renderChartLegend();

  ctx.strokeStyle = '#444'; ctx.beginPath(); ctx.moveTo(60, 30); ctx.lineTo(60, baseY); ctx.lineTo(canvas.width-30, baseY); ctx.stroke();
  ctx.fillStyle = '#aaa'; ctx.font = '14px Segoe UI'; ctx.fillText('Rozkład zwycięstw', 70, 30);

  const scale = (val) => val * (baseY - 60) / max;

  chartMeta = labels.map((label, i) => ({
    label,
    crown: crown[i],
    cossack: cossack[i],
    draw: draw[i],
    x: 70 + i*barW,
    width: barW-8,
    baseY,
    height: scale(cossack[i] + crown[i] + draw[i])
  }));

  let t = 0; const duration = 900; // ms
  const start = performance.now();

  function easeOutCubic(x){ return 1 - Math.pow(1 - x, 3); }

  function frame(now) {
    t = Math.min(1, (now - start) / duration);
    const e = easeOutCubic(t);
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.strokeStyle = '#444'; ctx.beginPath(); ctx.moveTo(60, 30); ctx.lineTo(60, baseY); ctx.lineTo(canvas.width-30, baseY); ctx.stroke();
    ctx.fillStyle = '#aaa'; ctx.font = '14px Segoe UI'; ctx.fillText('Rozkład zwycięstw', 70, 30);

    ctx.fillStyle = '#888'; ctx.font = '12px Segoe UI';
    const ticks = 5;
    for (let i=0;i<=ticks;i++) {
      const y = baseY - (i*(baseY-60)/ticks);
      const val = Math.round(i*max/ticks);
      ctx.strokeStyle = '#333'; ctx.beginPath(); ctx.moveTo(60, y); ctx.lineTo(canvas.width-30, y); ctx.stroke();
      ctx.fillText(val.toString(), 32, y+4);
    }

    labels.forEach((label, i) => {
      const x = 70 + i*barW;
      const cH = scale(cossack[i]) * e;
      const kH = scale(crown[i]) * e;
      const dH = scale(draw[i]) * e;

      ctx.fillStyle = '#1976d2'; ctx.fillRect(x, baseY - cH, barW-8, cH);
      ctx.fillStyle = '#d32f2f'; ctx.fillRect(x, baseY - cH - kH, barW-8, kH);
      ctx.fillStyle = '#777'; ctx.fillRect(x, baseY - cH - kH - dH, barW-8, dH);

      ctx.fillStyle = '#dcdcdc';
      ctx.font = '11px Segoe UI';
      ctx.textAlign = 'center';
      const lines = wrapLabel(label, Math.max(8, Math.floor((barW-8) / 7)));
      lines.forEach((line, idx) => {
        ctx.fillText(line, x + (barW-8)/2, baseY + 14 + idx*12);
      });

    });

    if (t < 1) requestAnimationFrame(frame);
  }

  requestAnimationFrame(frame);

  bindChartHover(canvas);
}

function bindChartHover(canvas) {
  if (!canvas) return;
  if (!canvas._hoverBound) {
    canvas.addEventListener('mousemove', handleChartHover);
    canvas.addEventListener('mouseleave', hideChartTooltip);
    canvas._hoverBound = true;
  }
}

function handleChartHover(evt) {
  if (!chartTooltipEl || !chartCanvas || !chartMeta.length) return;
  const rect = chartCanvas.getBoundingClientRect();
  const x = evt.clientX - rect.left;
  const y = evt.clientY - rect.top;
  const hovered = chartMeta.find(meta => (
    x >= meta.x && x <= meta.x + meta.width &&
    y >= meta.baseY - meta.height && y <= meta.baseY
  ));

  if (!hovered) {
    hideChartTooltip();
    return;
  }

  const html = `
    <strong>${hovered.label}</strong><br>
    Armia Koronna: ${hovered.crown}<br>
    Kozacy/Tatarzy: ${hovered.cossack}${hovered.draw ? `<br>Remis: ${hovered.draw}` : ''}
  `;
  chartTooltipEl.innerHTML = html;
  chartTooltipEl.classList.add('visible');
  chartTooltipEl.style.left = `${evt.clientX + 12}px`;
  chartTooltipEl.style.top = `${evt.clientY - 12}px`;
  chartTooltipEl.setAttribute('aria-hidden', 'false');
}

function hideChartTooltip() {
  if (!chartTooltipEl) return;
  chartTooltipEl.classList.remove('visible');
  chartTooltipEl.setAttribute('aria-hidden', 'true');
}

function renderChartLegend() {
  const container = document.getElementById('chartLegend');
  if (!container) return;
  const legend = [
    {name:'Kozacy/Tatarzy', col:'#1976d2'},
    {name:'Armia Koronna', col:'#d32f2f'},
    {name:'Remis', col:'#777'},
  ];
  container.innerHTML = legend
    .map(item => `<span class="legend-chip"><span class="legend-swatch" style="background:${item.col}"></span>${item.name}</span>`)
    .join('');
}

function wrapLabel(text, maxChars) {
  if (text.length <= maxChars) return [text];
  const words = text.split(' ');
  const lines = [];
  let current = '';
  words.forEach(word => {
    const tentative = current ? `${current} ${word}` : word;
    if (tentative.length > maxChars && current) {
      lines.push(current);
      current = word;
    } else {
      current = tentative;
    }
  });
  if (current) lines.push(current);
  return lines.slice(0, 2);
}

function renderResultsTable(data) {
  const container = document.getElementById('resultsTable');
  container.innerHTML = '';
  const table = document.createElement('table');
  const thead = document.createElement('thead');
  thead.innerHTML = '<tr><th>Czas</th><th>Scenariusz</th><th>Zwycięzca</th><th>Ocalałych</th><th>Koronna</th><th>Kozacy</th><th>Łącznie</th><th>Czas trwania</th><th>Kroki</th><th>Heatmapa</th></tr>';
  table.appendChild(thead);
  const tbody = document.createElement('tbody');

  data.slice().reverse().slice(0, 10).forEach(r => {
    const tr = document.createElement('tr');
    const winnerBadge = r.winner === 'Armia Koronna' ? 'badge crown' : (r.winner === 'Kozacy/Tatarzy' ? 'badge cossack' : 'badge draw');

    const heatmapLink = r.id ? `<a href="/heatmap/${r.id}" style="color: #4fc3f7; text-decoration: none; font-weight: bold;">Otwórz</a>` : '<span style="color:#555">-</span>';
    const duration = r.duration ? `${r.duration.toFixed(1)}s` : '-';
    const steps = r.total_steps || '-';

    tr.innerHTML = `<td>${r.timestamp}</td>
                    <td>${r.scenario_name || '—'}</td>
                    <td><span class="${winnerBadge}">${r.winner}</span></td>
                    <td>${r.survivors ?? 0}</td>
                    <td>${r.crown_count ?? 0}</td>
                    <td>${r.cossack_count ?? 0}</td>
                    <td>${r.total_agents ?? 0}</td>
                    <td>${duration}</td>
                    <td>${steps}</td>
                    <td>${heatmapLink}</td>`;
    tbody.appendChild(tr);
  });

  table.appendChild(tbody);
  container.appendChild(table);
}
