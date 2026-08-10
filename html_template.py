# html_template.py
# generate_html.py と generate_html_jp.py で共有する HTML テンプレート部品
# CSS・ヘッダー・共通JS を1箇所で管理する

COMMON_CSS = """
* {
  box-sizing: border-box;
}
html, body {
  touch-action: manipulation;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: #ffffff;
  margin: 0;
  padding: 0;
}
header {
  background-color: #31343C;
  color: white;
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-icon {
  width: 40px;
  height: 40px;
  object-fit: contain;
}
.header-logo-text {
  font-size: 1.2em;
  font-weight: 600;
  color: white;
}
.header-content {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}
.header-title {
  font-size: 1.8em;
  font-weight: 600;
  color: white;
  margin: 0;
}
.header-date {
  font-size: 1.0em;
  color: #ddd;
  margin-top: 4px;
}
@media (max-width: 768px) {
  .header-content {
    display: none;
  }
}
.controls {
  background-color: white;
  padding: 16px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-start;
  position: sticky;
  top: 0;
  z-index: 999;
}
.top-controls-row {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.mode-toggle {
  display: flex;
  gap: 10px;
}
.mode-btn {
  padding: 10px 20px;
  border: 2px solid #31343C;
  background-color: white;
  color: #31343C;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s;
}
.mode-btn.active {
  background-color: #31343C;
  color: white;
}
.country-tabs {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  font-weight: 600;
}
.country-link {
  color: #666;
  cursor: pointer;
  transition: color 0.2s;
  letter-spacing: 0.5px;
}
.country-link:hover {
  color: #31343C;
}
.country-link.active {
  color: #31343C;
  border-bottom: 2px solid #31343C;
  padding-bottom: 2px;
}
.country-divider {
  color: #bbb;
}
.week-nav {
  display: none;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.week-nav.active {
  display: flex;
}
.week-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}
.nav-btn {
  width: 40px;
  height: 30px;
  border: none;
  background-color: #f0f0f0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: #333;
}
.nav-btn:hover:not(:disabled) {
  background-color: #31343C;
  color: white;
  transform: scale(1.1);
}
.nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.week-label {
  font-weight: 600;
  font-size: 15px;
  color: #333;
  min-width: 200px;
  text-align: center;
}
.week-indicators {
  display: flex;
  gap: 8px;
}
.week-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #ddd;
  cursor: pointer;
  transition: all 0.3s;
}
.week-dot.active {
  background-color: #31343C;
  transform: scale(1.3);
}
.search-box {
  display: flex;
  width: 100%;
}
.search-box input {
  width: 100%;
  max-width: 400px;
  padding: 10px 16px;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
}
.search-box input:focus {
  outline: none;
  border-color: #31343C;
}
.container {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
  padding: 20px;
}
.week-row {
  display: contents;
}
@media (max-width: 768px) {
  .container {
    display: block;
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    -webkit-overflow-scrolling: touch;
    padding: 12px;
    scrollbar-width: thin;
    scrollbar-color: #31343C #f0f0f0;
  }
  .container::-webkit-scrollbar { height: 6px; }
  .container::-webkit-scrollbar-track { background: #f0f0f0; border-radius: 3px; }
  .container::-webkit-scrollbar-thumb { background: #31343C; border-radius: 3px; }
  .week-row {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
  }
  .day {
    min-width: 280px;
    flex-shrink: 0;
    scroll-snap-align: start;
  }
}
.day {
  background-color: rgba(255, 255, 255, 0.897);
  border-radius: 8px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  padding: 10px;
  min-height: 150px;
  display: flex;
  flex-direction: column;
}
.day.today {
  border: 3px solid #4CAF50;
  box-shadow: 0 4px 10px rgba(76, 175, 80, 0.3);
  background-color: #f0fff0;
}
.date {
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
  text-align: left;
}
.day.today .date {
  color: #4CAF50;
  font-size: 1.2em;
}
.logos {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.logo-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 90px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background-color: #fff;
  padding: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  transition: all 0.3s;
}
.logo-card.hidden { display: none; }
.logo-card img {
  width: 56px;
  height: 56px;
  object-fit: contain;
  margin-bottom: 6px;
  border-radius: 10%;
}
.symbol {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}
.no-earnings {
  font-size: 13px;
  color: #aaa;
  margin-top: 20px;
  text-align: center;
}
.more-count {
  margin-top: 8px;
  text-align: center;
  font-size: 12px;
  color: #666;
  font-weight: 600;
}
footer {
  text-align: center;
  font-size: 12px;
  color: #888;
  margin: 20px;
}
@media (max-width: 768px) {
  header { flex-direction: column; gap: 12px; }
  .header-left { width: 100%; justify-content: flex-start; display: none; }
  .header-content { position: static; transform: none; }
  .header-icon { width: 32px; height: 32px; }
  .header-logo-text { font-size: 1.0em; }
  .header-title { font-size: 1.2em; }
  .header-title.hidden { display: none; }
  .header-date { font-size: 0.9em; }
  .day { min-height: 120px; padding: 8px; }
  .logos { grid-template-columns: repeat(3, 1fr); gap: 6px; }
  .logo-card { height: 70px; }
  .logo-card img { width: 40px; height: 40px; }
  .symbol { font-size: 12px; }
  .mode-btn { padding: 8px 16px; font-size: 14px; }
  .week-label { min-width: 180px; font-size: 14px; }
}
@media (max-width: 480px) {
  .day { min-width: 260px; }
  .week-label { min-width: 160px; font-size: 13px; }
}
.weekday-header { display: contents; }
.weekday-cell {
  background-color: #31343C;
  color: white;
  padding: 4px;
  text-align: center;
  font-weight: 600;
  font-size: 16px;
}
@media (max-width: 768px) {
  .weekday-header { display: flex; gap: 8px; margin-bottom: 8px; }
  .weekday-cell { min-width: 280px; flex-shrink: 0; font-size: 14px; padding: 8px 4px; text-align: center; }
}
@media (max-width: 480px) {
  .weekday-cell { min-width: 260px; }
}
.logo-card.favorite {
  border: 2px solid #f0a500;
  background-color: #fffbf0;
  box-shadow: 0 2px 8px rgba(240, 165, 0, 0.35);
}
.logo-card.favorite .symbol {
  color: #b87800;
  font-weight: 700;
}
.logo-card.unconfirmed {
  position: relative;
  outline: 2px dashed #58799d;
  outline-offset: -4px;
}
.logo-card.unconfirmed::after {
  content: "TBD";
  position: absolute;
  top: 4px;
  right: 4px;
  padding: 2px 4px;
  border-radius: 999px;
  background-color: #385a7c;
  color: #fff;
  font-size: 8px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.03em;
  pointer-events: none;
}
"""


def build_html_head(title: str, lang: str = "en") -> str:
    """<head> セクションを生成する"""
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>{title}</title>
<style>
{COMMON_CSS}
</style>
</head>
"""


def build_header(title: str, date_str: str) -> str:
    """ページ上部のヘッダーを生成する"""
    return f"""<header>
  <div class="header-left">
    <img src="assets/icon.png" alt="Market Time Zen" class="header-icon">
    <span class="header-logo-text">Market Time Zen</span>
  </div>
  <div class="header-content">
    <div class="header-title">{title}</div>
    <div class="header-date">{date_str}</div>
  </div>
</header>
"""


def build_controls(active_market: str, search_placeholder: str) -> str:
    """
    コントロールバー（Monthly/Weekly切替 + New York/Tokyo切替 + 検索欄）を生成する。
    active_market: 'us' または 'jp'
    """
    ny_active  = 'active' if active_market == 'us' else ''
    jp_active  = 'active' if active_market == 'jp' else ''

    return f"""<div class="controls">
  <div class="top-controls-row">
    <div class="mode-toggle">
      <button class="mode-btn active" onclick="switchMode('monthly')">Monthly</button>
      <button class="mode-btn" onclick="switchMode('weekly')">Weekly</button>
    </div>
    <div class="country-tabs">
      <span class="country-link {ny_active}" onclick="goToMarket('index.html')">New York</span>
      <span class="country-divider">|</span>
      <span class="country-link {jp_active}" onclick="goToMarket('japan.html')">Tokyo</span>
    </div>
  </div>
  <div class="week-nav" id="weekNav">
    <div class="week-controls">
      <button class="nav-btn" id="prevWeek" onclick="changeWeek(-1)">‹</button>
      <span class="week-label" id="weekLabel">Week 1</span>
      <button class="nav-btn" id="nextWeek" onclick="changeWeek(1)">›</button>
    </div>
    <div class="week-indicators" id="weekDots"></div>
  </div>
  <div class="search-box">
    <input type="text" id="searchInput" placeholder="{search_placeholder}" oninput="searchSymbols()">
  </div>
</div>
"""


def build_common_js() -> str:
    """両ページ共通の JavaScript を返す（favorites取得・ページ遷移・週操作など）"""
    return """
function getFavorites() {
  const params = new URLSearchParams(window.location.search);
  const fav = params.get('favorites');
  return fav ? fav.split(',').map(s => s.trim().toUpperCase()).filter(Boolean) : [];
}
const favorites = getFavorites();

// favoritesパラメータを引き継いでページ遷移する
function goToMarket(page) {
  const params = new URLSearchParams(window.location.search);
  const fav = params.get('favorites');
  window.location.href = fav ? `${page}?favorites=${fav}` : page;
}

function updateHeaderHeight() {
  const h = document.querySelector('header').offsetHeight;
  document.documentElement.style.setProperty('--header-height', h + 'px');
}

function findCurrentWeek() {
  const today = new Date().toISOString().split('T')[0];
  const todayDay = new Date().getDay();
  for (let i = 0; i < weeks.length; i++) {
    const weekDates = weeks[i];
    if (todayDay >= 1 && todayDay <= 5) {
      if (weekDates.includes(today)) return i;
    } else {
      if (weekDates[0] > today) return i;
    }
  }
  return 0;
}

function scrollToCurrentWeek() {
  if (currentMode !== 'monthly') return;
  const allWeekRows = document.querySelectorAll('.week-row-wrapper');
  if (allWeekRows.length === 0) return;
  const targetRow = allWeekRows[currentWeek] || allWeekRows[0];
  if (!targetRow) return;
  const headerEl = document.querySelector('header');
  const controlsEl = document.querySelector('.controls');
  const offset = (headerEl ? headerEl.offsetHeight : 0) + (controlsEl ? controlsEl.offsetHeight : 0);
  const top = targetRow.getBoundingClientRect().top + window.scrollY - offset - 8;
  window.scrollTo({ top: Math.max(0, top), behavior: 'instant' });
}

function switchMode(mode) {
  currentMode = mode;
  document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.mode-btn').forEach(btn => {
    const label = btn.textContent.trim();
    if ((mode === 'monthly' && label === 'Monthly') ||
        (mode === 'weekly'  && label === 'Weekly'))  {
      btn.classList.add('active');
    }
  });
  if (mode === 'weekly') {
    document.getElementById('weekNav').classList.add('active');
    renderWeekDots();
  } else {
    document.getElementById('weekNav').classList.remove('active');
  }
  renderCalendar();
}

function renderWeekDots() {
  const dotsContainer = document.getElementById('weekDots');
  dotsContainer.innerHTML = '';
  weeks.forEach((week, idx) => {
    const dot = document.createElement('div');
    dot.className = 'week-dot' + (idx === currentWeek ? ' active' : '');
    dot.onclick = () => { currentWeek = idx; renderCalendar(); };
    dotsContainer.appendChild(dot);
  });
}

function changeWeek(delta) {
  currentWeek = Math.max(0, Math.min(weeks.length - 1, currentWeek + delta));
  renderCalendar();
}

function formatDateRange(dates) {
  if (!dates || dates.length === 0) return '';
  const start = new Date(dates[0] + 'T00:00:00');
  const end   = new Date(dates[dates.length - 1] + 'T00:00:00');
  return `${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${end.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
}

document.addEventListener('DOMContentLoaded', updateHeaderHeight);
window.addEventListener('resize', updateHeaderHeight);
"""
