const STORAGE_KEYS = {
  clubs: 'ntvs-clubs',
  players: 'ntvs-players',
};

const defaultStats = () => ({ kills: 0, digs: 0, aces: 0, blocks: 0, assists: 0 });

const state = {
  clubs: [],
  players: [],
};

const heroClubCount = document.getElementById('hero-club-count');
const heroPlayerCount = document.getElementById('hero-player-count');
const clubForm = document.getElementById('club-form');
const clubList = document.getElementById('club-list');
const playerForm = document.getElementById('player-form');
const playerTableBody = document.getElementById('player-table-body');
const playerClubSelect = document.getElementById('player-club');
const exportButton = document.getElementById('export-csv');
const importInput = document.getElementById('import-csv');
const exportPreview = document.getElementById('export-preview');
const resetButton = document.getElementById('reset-data');

function loadData() {
  try {
    state.clubs = JSON.parse(localStorage.getItem(STORAGE_KEYS.clubs)) || [];
    state.players = JSON.parse(localStorage.getItem(STORAGE_KEYS.players)) || [];
  } catch (error) {
    console.error('Failed to load data', error);
  }
}

function saveData() {
  localStorage.setItem(STORAGE_KEYS.clubs, JSON.stringify(state.clubs));
  localStorage.setItem(STORAGE_KEYS.players, JSON.stringify(state.players));
}

function renderSnapshot() {
  heroClubCount.textContent = state.clubs.length;
  heroPlayerCount.textContent = state.players.length;
}

function renderClubs() {
  clubList.innerHTML = '';
  playerClubSelect.innerHTML = '<option value="" disabled selected>Select a club</option>';

  state.clubs.forEach((club) => {
    const card = document.createElement('div');
    card.className = 'card';
    const count = state.players.filter((p) => p.clubId === club.id).length;
    card.innerHTML = `
      <h3>${club.name}</h3>
      <p class="subtitle">${club.division || 'Division not set'}</p>
      <div class="badge">${count} player${count === 1 ? '' : 's'}</div>
    `;
    clubList.appendChild(card);

    const option = document.createElement('option');
    option.value = club.id;
    option.textContent = club.name;
    playerClubSelect.appendChild(option);
  });

  renderSnapshot();
}

function renderPlayers() {
  playerTableBody.innerHTML = '';

  state.players.forEach((player) => {
    const club = state.clubs.find((c) => c.id === player.clubId);
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${player.name}</td>
      <td>${club ? club.name : 'Unassigned'}</td>
      <td>${player.number ?? ''}</td>
      <td>${player.position || ''}</td>
      <td>${player.stats.kills}</td>
      <td>${player.stats.digs}</td>
      <td>${player.stats.aces}</td>
      <td>${player.stats.blocks}</td>
      <td>${player.stats.assists}</td>
    `;
    playerTableBody.appendChild(row);
  });

  renderSnapshot();
  exportPreview.textContent = buildCsv();
}

function buildCsv() {
  const header = ['Club', 'Player', 'Jersey', 'Position', 'Kills', 'Digs', 'Aces', 'Blocks', 'Assists'];
  const lines = [header.join(',')];

  state.players.forEach((player) => {
    const club = state.clubs.find((c) => c.id === player.clubId);
    const values = [
      club ? club.name : '',
      player.name,
      player.number ?? '',
      player.position || '',
      player.stats.kills,
      player.stats.digs,
      player.stats.aces,
      player.stats.blocks,
      player.stats.assists,
    ];
    lines.push(values.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(','));
  });

  return lines.join('\n');
}

function downloadCsv() {
  const csvContent = buildCsv();
  exportPreview.textContent = csvContent;
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', 'ntvs-stats.csv');
  link.click();
  URL.revokeObjectURL(url);
}

function importCsv(file) {
  const reader = new FileReader();
  reader.onload = (event) => {
    const text = event.target.result;
    const [headerLine, ...rows] = text.split(/\r?\n/).filter(Boolean);
    const headers = headerLine.split(',').map((h) => h.trim().replace(/\"/g, ''));
    const required = ['Club', 'Player', 'Jersey', 'Position', 'Kills', 'Digs', 'Aces', 'Blocks', 'Assists'];
    const isValid = required.every((col, idx) => headers[idx]?.toLowerCase() === col.toLowerCase());

    if (!isValid) {
      alert('CSV format mismatch. Please use the provided template.');
      return;
    }

    rows.forEach((row) => {
      const cols = row.match(/("[^"]*"|[^,]+)/g) || [];
      const [clubName, playerName, jersey, position, kills, digs, aces, blocks, assists] = cols.map((col) => col.replace(/^"|"$/g, ''));

      if (!playerName) return;

      let club = state.clubs.find((c) => c.name === clubName);
      if (!club && clubName) {
        club = { id: crypto.randomUUID(), name: clubName, division: '' };
        state.clubs.push(club);
      }

      const player = state.players.find((p) => p.name === playerName && p.clubId === club?.id);
      const stats = {
        kills: Number(kills) || 0,
        digs: Number(digs) || 0,
        aces: Number(aces) || 0,
        blocks: Number(blocks) || 0,
        assists: Number(assists) || 0,
      };

      if (player) {
        player.number = jersey;
        player.position = position;
        player.stats = stats;
      } else {
        state.players.push({
          id: crypto.randomUUID(),
          name: playerName,
          number: jersey,
          position,
          clubId: club?.id || null,
          stats,
        });
      }
    });

    saveData();
    renderClubs();
    renderPlayers();
  };
  reader.readAsText(file);
}

function handleClubSubmit(event) {
  event.preventDefault();
  const name = document.getElementById('club-name').value.trim();
  const division = document.getElementById('club-division').value.trim();

  if (!name) return;

  state.clubs.push({ id: crypto.randomUUID(), name, division });
  saveData();
  renderClubs();
  event.target.reset();
}

function handlePlayerSubmit(event) {
  event.preventDefault();
  const name = document.getElementById('player-name').value.trim();
  const number = document.getElementById('player-number').value;
  const position = document.getElementById('player-position').value.trim();
  const clubId = document.getElementById('player-club').value;

  if (!name || !clubId) return;

  state.players.push({
    id: crypto.randomUUID(),
    name,
    number,
    position,
    clubId,
    stats: defaultStats(),
  });

  saveData();
  renderPlayers();
  event.target.reset();
  const [firstOption] = playerClubSelect.querySelectorAll('option');
  if (firstOption) {
    firstOption.selected = true;
  }
}

function resetData() {
  if (!confirm('Reset all clubs and players?')) return;
  state.clubs = [];
  state.players = [];
  saveData();
  renderClubs();
  renderPlayers();
}

function init() {
  loadData();
  renderClubs();
  renderPlayers();

  clubForm.addEventListener('submit', handleClubSubmit);
  playerForm.addEventListener('submit', handlePlayerSubmit);
  exportButton.addEventListener('click', downloadCsv);
  importInput.addEventListener('change', (event) => {
    const [file] = event.target.files;
    if (file) importCsv(file);
  });
  resetButton.addEventListener('click', resetData);
}

window.addEventListener('DOMContentLoaded', init);
