let STATS = ["HP", "Str", "Mag", "Skl", "Spd", "Lck", "Def", "Res"];
let STAT_COLORS = {
    "HP": "#22c55e",
    "Str": "#ef4444",
    "Mag": "#a855f7",
    "Skl": "#06b6d4",
    "Spd": "#eab308",
    "Lck": "#f97316",
    "Def": "#3b82f6",
    "Res": "#ec4899",
    "Bld": "#94a3b8",
    "Mov": "#14b8a6"
};

// --- Per-game look and starting character ---
// [starting character, accent, secondary accent, accent as "r, g, b", page halo colour]
const GAME_SETTINGS = {
    fe5: ["Leaf", "#10b981", "#f59e0b", "16, 185, 129", "rgba(16, 185, 129, 0.25)"],
    fe6: ["Roy", "#f59e0b", "#ef4444", "245, 158, 11", "rgba(245, 158, 11, 0.15)"],
    fe7: ["Eliwood", "#10b981", "#06b6d4", "16, 185, 129", "rgba(16, 80, 60, 0.2)"],
    fe8: ["Eirika", "#8b5cf6", "#d946ef", "139, 92, 246", "rgba(139, 92, 246, 0.2)"],
    fe9: ["Ike", "#10b981", "#fbbf24", "16, 185, 129", "rgba(16, 185, 129, 0.2)"],
    fe10: ["Micaiah", "#f97316", "#fbbf24", "249, 115, 22", "rgba(249, 115, 22, 0.2)"],
    fe11: ["Marth", "#06b6d4", "#3b82f6", "6, 182, 212", "rgba(6, 182, 212, 0.25)"],
    fe12: ["Shiida", "#3b82f6", "#8b5cf6", "59, 130, 246", "rgba(59, 130, 246, 0.2)"]
};

// --- State Variables ---
// All numbers come precomputed from average_stats_data.js (python calculate_stats.py)
let currentGame = "";
let activeStatsData = {};
let currentCharacterName = "Shiida";
let activeTabId = "reclass-list-view";
let checkedChartStats = {};
let selectedSimClass = "";
let selectedBstClass = "";
let bstClassRankings = {};
let leaderboardOpen = false;
let rankAllClasses = false;

// Sorting State for Reclass Statistics Table & BST Leaderboard
let currentSortColumn = "class";
let currentSortOrder = "asc";
let currentBstSortColumn = "bst";
let currentBstSortOrder = "desc";

const bstOf = classData => STATS.reduce((sum, s) => sum + classData.stats[s], 0);

// Stats the leaderboard leaves out of its BST; keyed by name so it outlives board and game switches
const bstExcludedStats = new Set();
const bstStats = () => STATS.filter(s => !bstExcludedStats.has(s));

// Caps of the class a path ends in, keyed by stat.
// A segment is [class, labelPrefix, firstLevel, rows, start, growths, caps].
const capsOf = classData => Object.fromEntries(STATS.map((s, i) => [s, classData.segs.at(-1)[6][i]]));

// A cap of 0 means the class does not use that stat
const atCap = (value, cap) => cap > 0 && value >= cap;

function computeBSTRankings() {
    bstClassRankings = {};

    Object.entries(activeStatsData).forEach(([charName, charData]) => {
        // A custom unit has no default path, and rank-all games list every path; both are ranked
        // only in final classes: promoted, or special classes that never promote
        const classNames = charName.includes("My Unit") || rankAllClasses
            ? Object.keys(charData.classes).filter(clsName => charData.classes[clsName].tier)
            : [charData.direct];

        classNames.forEach(clsName => {
            const classData = charData.classes[clsName];
            if (!classData) return;
            // Board = class the path ends in, without its gender tag, so several paths share a board;
            // per-row cap stars still use each row's own caps
            (bstClassRankings[classData.segs.at(-1)[0].replace(/ \([MF]\)$/, "")] ||= []).push({
                name: charName,
                isFemale: charData.is_female,
                classPath: classData.class_path,
                finalLevel: classData.final_level,
                tier: classData.tier,
                stats: classData.stats,
                caps: capsOf(classData),
                bst: bstStats().reduce((sum, s) => sum + classData.stats[s], 0)
            });
        });
    });

    Object.keys(bstClassRankings).forEach(className => {
        bstClassRankings[className].sort((a, b) => b.bst - a.bst);
        bstClassRankings[className].forEach((item, idx) => {
            item.originalRank = idx + 1;
        });
    });
}

function handleBSTHeaderClick(colKey) {
    if (currentBstSortColumn === colKey) {
        currentBstSortOrder = currentBstSortOrder === "asc" ? "desc" : "asc";
    } else {
        currentBstSortColumn = colKey;
        currentBstSortOrder = (colKey === "name" || colKey === "path") ? "asc" : "desc";
    }
    renderBSTLeaderboard(selectedBstClass);
}

function updateBSTTableHeaderIcons() {
    const cols = ["rank", "name", "path", "level", "bst", ...STATS];
    cols.forEach(col => {
        const iconEl = document.getElementById(`sort-icon-bst-${col}`);
        if (iconEl) {
            if (currentBstSortColumn === col) {
                iconEl.innerText = currentBstSortOrder === "asc" ? " ▲" : " ▼";
                iconEl.style.color = "#fbbf24";
                iconEl.style.fontSize = "0.7rem";
            } else {
                iconEl.innerText = "";
            }
        }
    });
}

function renderBSTTableHeaders() {
    const tr = document.getElementById("bst-table-headers");
    if (!tr) return;

    let html = `
        <th onclick="handleBSTHeaderClick('rank')" style="width: 50px;"># <span id="sort-icon-bst-rank"></span></th>
        <th onclick="handleBSTHeaderClick('name')">Character <span id="sort-icon-bst-name"></span></th>
        <th onclick="handleBSTHeaderClick('path')">Class Path <span id="sort-icon-bst-path"></span></th>
        <th onclick="handleBSTHeaderClick('level')">Max Lv <span id="sort-icon-bst-level"></span></th>
        <th onclick="handleBSTHeaderClick('bst')">BST <span id="sort-icon-bst-bst"></span></th>
    `;

    bstStats().forEach(s => {
        html += `<th onclick="handleBSTHeaderClick('${s}')">${s} <span id="sort-icon-bst-${s}"></span></th>`;
    });

    tr.innerHTML = html;
    updateBSTTableHeaderIcons();
}

function renderBSTStatFilter() {
    const container = document.getElementById("bst-stat-filter");
    if (!container) return;

    let html = `<span class="text-sub">Count in BST:</span>`;
    STATS.forEach(s => {
        const color = STAT_COLORS[s] || `var(--stat-${s.toLowerCase()})`;
        const on = !bstExcludedStats.has(s);
        html += `
            <label class="stat-checkbox-label ${on ? "checked" : ""}">
                <span class="stat-dot" style="background-color: ${color}; border-color: ${color}; box-shadow: 0 0 6px ${color}55;"></span>
                <input type="checkbox" class="stat-checkbox" ${on ? "checked" : ""} onchange="toggleBstStat('${s}')">
                <span style="font-weight: 500;">${s}</span>
            </label>
        `;
    });
    container.innerHTML = html;
}

function toggleBstStat(s) {
    if (!bstExcludedStats.delete(s)) bstExcludedStats.add(s);
    computeBSTRankings();
    initBSTLeaderboard();
}

function initBSTLeaderboard() {
    // A removed column cannot stay the sort key
    if (bstExcludedStats.has(currentBstSortColumn)) {
        currentBstSortColumn = "bst";
        currentBstSortOrder = "desc";
    }
    renderBSTStatFilter();
    renderBSTTableHeaders();

    const gridContainer = document.getElementById("bst-class-grid-container");
    if (!gridContainer) return;
    gridContainer.innerHTML = "";

    const sortedClasses = Object.keys(bstClassRankings).sort();
    if (sortedClasses.length === 0) return;

    if (!selectedBstClass || !sortedClasses.includes(selectedBstClass)) {
        selectedBstClass = sortedClasses.includes("Falcon Knight") ? "Falcon Knight" : (sortedClasses.includes("Falcoknight") ? "Falcoknight" : (sortedClasses.includes("Paladin") ? "Paladin" : sortedClasses[0]));
    }

    sortedClasses.forEach(className => {
        const list = bstClassRankings[className];
        const leader = list[0];
        const card = document.createElement("div");
        card.className = `bst-class-card ${className === selectedBstClass ? 'active' : ''}`;
        card.id = `bst-cls-card-${className.replace(/[^a-zA-Z0-9]/g, '_')}`;
        card.onclick = () => selectBstClass(className);

        card.innerHTML = `
            <div class="bst-class-card-left">
                <span class="bst-class-card-name" title="${className}">${className}</span>
                <span class="bst-class-card-units">${new Set(list.map(r => r.name)).size} unit${new Set(list.map(r => r.name)).size === 1 ? '' : 's'}</span>
            </div>
            <div class="bst-class-card-leader">
                <span class="bst-class-card-leader-name" title="${leader.name}">${leader.name}</span>
                <span class="bst-class-card-leader-bst">${leader.bst.toFixed(1)} BST</span>
            </div>
        `;

        gridContainer.appendChild(card);
    });

    renderBSTLeaderboard(selectedBstClass);
}

function selectBstClass(className) {
    selectedBstClass = className;
    document.querySelectorAll(".bst-class-card").forEach(item => item.classList.remove("active"));
    const safeId = `bst-cls-card-${className.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const card = document.getElementById(safeId);
    if (card) card.classList.add("active");
    renderBSTLeaderboard(className);
}

function renderBSTLeaderboard(className) {
    const rawList = bstClassRankings[className];
    if (!rawList || rawList.length === 0) return;

    const titleEl = document.getElementById("bst-class-title");
    const maxLvEl = document.getElementById("bst-class-max-lv");
    const descEl = document.getElementById("bst-class-desc");
    const tbody = document.getElementById("bst-table-body");
    if (!tbody) return;

    titleEl.innerText = `${className} Leaderboard`;
    maxLvEl.innerText = `Max Lv: ${rawList[0].finalLevel}`;
    // Rows may end at different levels (FE8); a single header badge would mislead.
    maxLvEl.style.display = rawList.every(r => r.finalLevel === rawList[0].finalLevel) ? "" : "none";

    const badgeClass = rawList[0].tier;
    maxLvEl.className = `max-lv-badge ${badgeClass}`;

    descEl.innerText = rankAllClasses
        ? `Every class path playable characters can take to end as ${className}. Click any column header to sort.`
        : `Playable characters who stick to their default classes and promote directly to ${className}. Click any column header to sort.`;
    const left = STATS.filter(s => bstExcludedStats.has(s));
    if (left.length) descEl.innerText += ` BST without ${left.join(", ")}.`;

    // Sort list based on currentBstSortColumn and currentBstSortOrder
    const list = [...rawList];
    list.sort((a, b) => {
        let valA, valB;
        if (currentBstSortColumn === "rank") {
            valA = a.originalRank;
            valB = b.originalRank;
        } else if (currentBstSortColumn === "name") {
            valA = a.name;
            valB = b.name;
            return currentBstSortOrder === "asc" ? valA.localeCompare(valB) : valB.localeCompare(valA);
        } else if (currentBstSortColumn === "path") {
            valA = a.classPath || "";
            valB = b.classPath || "";
            return currentBstSortOrder === "asc" ? valA.localeCompare(valB) : valB.localeCompare(valA);
        } else if (currentBstSortColumn === "level") {
            valA = getLevelSortValue(a.finalLevel);
            valB = getLevelSortValue(b.finalLevel);
        } else if (currentBstSortColumn === "bst") {
            valA = a.bst;
            valB = b.bst;
        } else {
            valA = (a.stats && a.stats[currentBstSortColumn] !== undefined) ? a.stats[currentBstSortColumn] : 0;
            valB = (b.stats && b.stats[currentBstSortColumn] !== undefined) ? b.stats[currentBstSortColumn] : 0;
        }

        if (currentBstSortOrder === "asc") {
            return valA - valB;
        } else {
            return valB - valA;
        }
    });

    tbody.innerHTML = "";

    list.forEach((item, index) => {
        const isBstLeader = item.originalRank === 1;
        const tr = document.createElement("tr");
        if (isBstLeader) {
            tr.className = "selected";
        }

        const dotClass = item.isFemale ? 'gender-female' : 'gender-male';

        let tdHTML = `
            <td style="font-weight: 700; color: var(--text-secondary); text-align: center;">
                ${isBstLeader ? '👑' : (index + 1)}
            </td>
            <td>
                <div class="class-td-name" onclick="loadCharacterDetails('${item.name.replace(/'/g, "\\'")}'); showMainOnPhone()">
                    <span class="char-item-gender-dot ${dotClass}"></span>
                    <span style="font-weight: 600;">${item.name}</span>
                    ${isBstLeader ? ' <span style="color:#fbbf24; font-size:0.75rem;">★</span>' : ''}
                </div>
            </td>
            <td><div class="class-td-path">${item.classPath}</div></td>
            <td><span class="max-lv-badge ${badgeClass}">${item.finalLevel}</span></td>
            <td style="font-weight: 700; color: #fbbf24;">${item.bst.toFixed(1)}</td>
        `;

        bstStats().forEach(s => {
            const val = (item.stats && item.stats[s] !== undefined) ? item.stats[s] : 0;
            const isCapped = atCap(val, item.caps[s]);

            tdHTML += `
                <td class="${isCapped ? 'cap-cell' : ''}">
                    ${val.toFixed(1)}
                    ${isCapped ? '<span style="font-size:0.6rem; vertical-align:middle; margin-left:2px;">★</span>' : ''}
                </td>
            `;
        });

        tr.innerHTML = tdHTML;
        tbody.appendChild(tr);
    });

    updateBSTTableHeaderIcons();
}

function renderTableHeaders() {
    const tableHeaders = document.getElementById("table-headers");
    if (!tableHeaders) return;

    let html = `
        <th onclick="handleHeaderClick('class')">Class Path <span id="sort-icon-class"></span></th>
        <th onclick="handleHeaderClick('level')">Max Level <span id="sort-icon-level"></span></th>
        <th onclick="handleHeaderClick('bst')">BST <span id="sort-icon-bst"></span></th>
    `;

    STATS.forEach(s => {
        html += `<th onclick="handleHeaderClick('${s}')">${s} <span id="sort-icon-${s}"></span></th>`;
    });

    tableHeaders.innerHTML = html;
}

function renderSimTableHeaders() {
    const tr = document.querySelector("#simulator-view table thead tr");
    if (!tr) return;

    let html = `
        <th>Level</th>
        <th>Class</th>
    `;
    STATS.forEach(s => {
        html += `<th>${s}</th>`;
    });
    tr.innerHTML = html;
}

function renderChartCheckboxes() {
    const container = document.getElementById("chart-checkboxes-container");
    if (!container) return;

    let html = "";
    STATS.forEach(s => {
        const color = STAT_COLORS[s] || `var(--stat-${s.toLowerCase()})`;
        const isChecked = checkedChartStats[s] ? "checked" : "";
        const activeClass = checkedChartStats[s] ? "checked" : "";
        html += `
            <label class="stat-checkbox-label ${activeClass}" id="lbl-chk-${s}">
                <span class="stat-dot" style="background-color: ${color}; border-color: ${color}; box-shadow: 0 0 6px ${color}55;"></span>
                <input type="checkbox" class="stat-checkbox" id="chk-${s}" ${isChecked} onchange="toggleChartStat('${s}')">
                <span style="font-weight: 500;">${s}</span>
            </label>
        `;
    });
    container.innerHTML = html;
}

function setAllChartStats(selectAll) {
    STATS.forEach(s => {
        checkedChartStats[s] = selectAll;
        const chk = document.getElementById(`chk-${s}`);
        if (chk) chk.checked = selectAll;
        const lbl = document.getElementById(`lbl-chk-${s}`);
        if (lbl) {
            if (selectAll) lbl.classList.add("checked");
            else lbl.classList.remove("checked");
        }
    });
    renderSVGChart();
}

// --- Switch Games ---
function switchGame(gameId) {
    currentGame = gameId;
    activeStatsData = AVERAGE_STATS_DATA[currentGame].characters;
    STATS = AVERAGE_STATS_DATA[currentGame].stats;
    rankAllClasses = AVERAGE_STATS_DATA[currentGame].rank_all_classes;
    const wasOpen = leaderboardOpen;
    document.getElementById("bst-heading").innerText = rankAllClasses ? "BST Leaderboard" : "Direct Promotion BST Leaderboard";
    document.getElementById("bst-subheading").innerText = (rankAllClasses
        ? "Every promotion path each character can take, grouped by the final class it ends in. "
        : "Comparing characters when they stick to their default starting classes and promote directly. ")
        + "Click any column header to sort by BST or individual stats.";
    checkedChartStats = Object.fromEntries(STATS.map(s => [s, true]));

    // Keep the select dropdown value in sync with currentGame
    const selector = document.getElementById("game-selector");
    if (selector && selector.value !== gameId) {
        selector.value = gameId;
    }

    // Clear search and filters
    document.getElementById("search-bar").value = "";
    document.getElementById("filter-gender").value = "all";
    document.getElementById("filter-pool").value = "all";
    const tableFilter = document.getElementById("filter-table-tier");
    if (tableFilter) {
        tableFilter.value = "all";
    }
    const chartFilter = document.getElementById("filter-chart-tier");
    if (chartFilter) {
        chartFilter.value = "all";
    }

    // Theme colors transition
    const [defaultCharacter, primary, secondary, glow, halo] = GAME_SETTINGS[currentGame];
    const root = document.documentElement;
    root.style.setProperty('--accent-primary', primary);
    root.style.setProperty('--accent-secondary', secondary);

    // Recompute rankings
    computeBSTRankings();

    // Rebuild character list
    initSidebarList();

    currentCharacterName = defaultCharacter;

    // Redraw dynamic page parts
    renderTableHeaders();
    renderSimTableHeaders();
    renderBSTTableHeaders();
    renderChartCheckboxes();

    loadCharacterDetails(currentCharacterName);

    // loadCharacterDetails closes the leaderboard; restore it (rebuilds the boards)
    setLeaderboardOpen(wasOpen);
}

// On phones the sidebar sits above the content, so jump down to what was just picked
function showMainOnPhone() {
    if (typeof matchMedia === "function" && matchMedia("(max-width: 760px)").matches) {
        document.querySelector(".main-content").scrollIntoView({ behavior: "smooth" });
    }
}

// --- Leaderboard toggle: replaces the character page in the main area ---
function setLeaderboardOpen(open) {
    leaderboardOpen = open;
    document.querySelector(".main-content").classList.toggle("leaderboard-open", open);
    document.getElementById("bst-toggle").setAttribute("aria-pressed", String(open));
    if (open) initBSTLeaderboard();
}

// --- Initialization ---
window.addEventListener("DOMContentLoaded", () => {
    const selector = document.getElementById("game-selector");
    const initialGame = selector ? selector.value : "fe5";
    switchGame(initialGame);

    // Search filter event listeners
    document.getElementById("search-bar").addEventListener("input", filterSidebarList);
    document.getElementById("filter-gender").addEventListener("change", filterSidebarList);
    document.getElementById("filter-pool").addEventListener("change", filterSidebarList);

    // Re-render responsive chart on window resize
    window.addEventListener("resize", () => {
        if (activeTabId === "visual-chart-view") {
            renderSVGChart();
        }
    });
});

// --- Switch Tabs ---
function switchTab(viewId, btnEl) {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".view-section").forEach(s => s.classList.remove("active"));

    btnEl.classList.add("active");
    document.getElementById(viewId).classList.add("active");
    activeTabId = viewId;

    if (viewId === "visual-chart-view") {
        renderSVGChart();
    }
}

// --- Render Sidebar List ---
function initSidebarList() {
    const container = document.getElementById("char-list-container");
    container.innerHTML = "";

    Object.keys(activeStatsData).sort().forEach(name => {
        const data = activeStatsData[name];
        const safeId = `sidebar-char-${name.replace(/[^a-zA-Z0-9]/g, '_')}`;

        const item = document.createElement("div");
        item.className = `character-item ${name === currentCharacterName ? 'active' : ''}`;
        item.id = safeId;
        item.onclick = () => { loadCharacterDetails(name); showMainOnPhone(); };

        const dotClass = data.is_female ? 'gender-female' : 'gender-male';

        item.innerHTML = `
            <div class="char-item-info">
                <div class="char-item-name">
                    <span class="char-item-gender-dot ${dotClass}"></span>
                    ${name}
                </div>
                <div class="char-item-class">${data.default_class}</div>
            </div>
            <span class="char-item-level-badge">Lv ${data.join_lv}</span>
        `;
        container.appendChild(item);
    });
}

// --- Filter Sidebar List ---
function filterSidebarList() {
    const query = document.getElementById("search-bar").value.toLowerCase();
    const genderFilter = document.getElementById("filter-gender").value;
    const poolFilter = document.getElementById("filter-pool").value;

    Object.keys(activeStatsData).forEach(name => {
        const data = activeStatsData[name];
        const safeId = `sidebar-char-${name.replace(/[^a-zA-Z0-9]/g, '_')}`;
        const item = document.getElementById(safeId);
        if (!item) return;

        const matchesQuery = name.toLowerCase().includes(query) || data.default_class.toLowerCase().includes(query);

        let matchesGender = true;
        if (genderFilter === "female") matchesGender = data.is_female;
        if (genderFilter === "male") matchesGender = !data.is_female;

        let matchesPool = true;
        if (poolFilter === "special") {
            matchesPool = data.special;
        } else if (poolFilter === "cavalry") {
            matchesPool = data.default_class.includes("Pegasus") || data.default_class.includes("Cavalier") || data.default_class.includes("Draco") || data.default_class.includes("Paladin") || data.default_class.includes("Nomad") || data.default_class.includes("Rider") || data.default_class.includes("Valkyri") || data.default_class.includes("Knight") || data.default_class.includes("Ranger") || data.default_class.includes("Falcon");
        } else if (poolFilter === "magic") {
            matchesPool = data.default_class.includes("Mage") || data.default_class.includes("Cleric") || data.default_class.includes("Curate") || data.default_class.includes("Bishop") || data.default_class.includes("Sage") || data.default_class.includes("Shaman") || data.default_class.includes("Druid") || data.default_class.includes("Priest") || data.default_class.includes("Troubadour") || data.default_class.includes("Monk") || data.default_class.includes("Archsage") || data.default_class.includes("Pupil") || data.default_class.includes("Summoner") || data.default_class.includes("Valkyri") || data.default_class.includes("Necromancer") || data.default_class.includes("Heron");
        } else if (poolFilter === "infantry") {
            matchesPool = !data.special && !data.default_class.includes("Pegasus") && !data.default_class.includes("Cavalier") && !data.default_class.includes("Draco") && !data.default_class.includes("Paladin") && !data.default_class.includes("Nomad") && !data.default_class.includes("Rider") && !data.default_class.includes("Mage") && !data.default_class.includes("Cleric") && !data.default_class.includes("Curate") && !data.default_class.includes("Shaman") && !data.default_class.includes("Druid") && !data.default_class.includes("Priest") && !data.default_class.includes("Troubadour") && !data.default_class.includes("Monk") && !data.default_class.includes("Archsage") && !data.default_class.includes("Pupil") && !data.default_class.includes("Summoner") && !data.default_class.includes("Valkyri") && !data.default_class.includes("Necromancer") && !data.default_class.includes("Falcon") && !data.default_class.includes("Ranger") && (!data.default_class.includes("Knight") || data.default_class === "Knight");
        }

        if (matchesQuery && matchesGender && matchesPool) {
            item.style.display = "flex";
        } else {
            item.style.display = "none";
        }
    });
}

// --- Load Character Details ---
function loadCharacterDetails(name) {
    currentCharacterName = name;
    if (leaderboardOpen) setLeaderboardOpen(false);

    // Update sidebar active classes
    document.querySelectorAll(".character-item").forEach(item => item.classList.remove("active"));
    const safeId = `sidebar-char-${name.replace(/[^a-zA-Z0-9]/g, '_')}`;
    const activeItem = document.getElementById(safeId);
    if (activeItem) activeItem.classList.add("active");

    const rawData = activeStatsData[name];
    if (!rawData) return;

    // Hero Banner Info
    document.getElementById("hero-char-name").innerText = name;
    document.getElementById("hero-gender").innerText = rawData.is_female ? "Female" : "Male";
    document.getElementById("hero-gender").className = `hero-badge hero-badge-gender ${rawData.is_female ? '' : 'male'}`;
    document.getElementById("hero-default-class").innerText = rawData.default_class;
    document.getElementById("hero-join-level").innerText = `Join Level: ${rawData.join_lv}`;

    // Render Base Stats & Growth Rates Progress Bars
    renderBasesAndGrowths(rawData);

    // Render Reclass Table
    renderReclassTable(name);

    // Populate simulator selectors
    initSimulator(name);

    // Render Visual Chart
    if (activeTabId === "visual-chart-view") {
        renderSVGChart();
    }
}

// --- Render Personal bases & Growths ---
function renderBasesAndGrowths(rawData) {
    const basesContainer = document.getElementById("personal-bases-container");
    const growthsContainer = document.getElementById("personal-growths-container");

    basesContainer.innerHTML = "";
    growthsContainer.innerHTML = "";

    STATS.forEach(s => {
        const baseVal = rawData.absolute_bases[s];
        const growthVal = rawData.base_growths[s];
        const color = STAT_COLORS[s];

        // Bases (max absolute base is generally around 15, clamp visual max to 18)
        const baseWidth = Math.min(100, (baseVal / 18) * 100);
        basesContainer.innerHTML += `
            <div class="personal-stat-row">
                <div class="stat-label-col"><span class="stat-dot" style="background-color: ${color}"></span>${s}</div>
                <div class="stat-bar-wrapper">
                    <div class="stat-bar-fill" style="background-color: ${color}; width: ${baseWidth}%"></div>
                </div>
                <div class="stat-value-col">${baseVal}</div>
            </div>
        `;

        // Growths (max growth can be up to 100%)
        const growthWidth = Math.min(100, growthVal);
        growthsContainer.innerHTML += `
            <div class="personal-stat-row">
                <div class="stat-label-col"><span class="stat-dot" style="background-color: ${color}"></span>${s}</div>
                <div class="stat-bar-wrapper">
                    <div class="stat-bar-fill" style="background-color: ${color}; width: ${growthWidth}%"></div>
                </div>
                <div class="stat-value-col">${growthVal}%</div>
            </div>
        `;
    });
}

// --- Helper functions for Sorting and Filtering ---
function getLevelSortValue(finalLevel) {
    if (finalLevel.includes("10/20/20")) return 50;
    if (finalLevel.includes("20/20")) return 40;
    if (finalLevel.includes("30")) return 30;
    if (finalLevel.includes("20")) return 20;
    return parseFloat(finalLevel) || 0;
}

function handleHeaderClick(colKey) {
    if (currentSortColumn === colKey) {
        // Toggle direction
        currentSortOrder = currentSortOrder === "asc" ? "desc" : "asc";
    } else {
        currentSortColumn = colKey;
        // Default to descending for numeric stats/BST so high stats appear at the top immediately!
        currentSortOrder = (colKey === "class") ? "asc" : "desc";
    }
    renderReclassTable(currentCharacterName);
}

function updateTableHeaderIcons() {
    const cols = ["class", "level", "bst", ...STATS];
    cols.forEach(col => {
        const iconEl = document.getElementById(`sort-icon-${col}`);
        if (iconEl) {
            if (currentSortColumn === col) {
                iconEl.innerText = currentSortOrder === "asc" ? " ▲" : " ▼";
                iconEl.style.color = "#fbbf24"; // Amber color to match dashboard accents
                iconEl.style.fontSize = "0.7rem";
            } else {
                iconEl.innerText = "";
            }
        }
    });
}

function filterClassesByTier(charData, classesList, tierFilter) {
    if (!tierFilter || tierFilter === "all") return classesList;
    const tier = { promoted: "promo", base: "", special: "special" }[tierFilter];
    return classesList.filter(clsName => charData.classes[clsName].tier === tier);
}

// --- Render Reclass Table ---
function renderReclassTable(name) {
    const charData = activeStatsData[name];
    const tbody = document.getElementById("reclass-table-body");
    tbody.innerHTML = "";

    const tierFilter = document.getElementById("filter-table-tier") ? document.getElementById("filter-table-tier").value : "all";

    // 1. Filter Classes based on selected tier
    let classesList = filterClassesByTier(charData, Object.keys(charData.classes), tierFilter);

    // 2. Sort Classes based on active sorting criteria
    classesList.sort((a, b) => {
        const dataA = charData.classes[a];
        const dataB = charData.classes[b];

        let valA, valB;

        if (currentSortColumn === "class") {
            valA = a;
            valB = b;
        } else if (currentSortColumn === "level") {
            valA = getLevelSortValue(dataA.final_level);
            valB = getLevelSortValue(dataB.final_level);
        } else if (currentSortColumn === "bst") {
            valA = bstOf(dataA);
            valB = bstOf(dataB);
        } else {
            valA = dataA.stats[currentSortColumn];
            valB = dataB.stats[currentSortColumn];
        }

        if (currentSortColumn === "class") {
            if (currentSortOrder === "asc") {
                return valA.localeCompare(valB);
            } else {
                return valB.localeCompare(valA);
            }
        } else {
            if (currentSortOrder === "asc") {
                return valA - valB;
            } else {
                return valB - valA;
            }
        }
    });

    // 3. Render Table rows
    classesList.forEach(clsName => {
        const clsData = charData.classes[clsName];
        const classCaps = capsOf(clsData);

        // Determine Row Style
        const isDefault = clsName === charData.default_class || clsName === charData.direct;
        const rowClass = isDefault ? 'selected' : '';

        const tr = document.createElement("tr");
        tr.className = rowClass;

        const badgeClass = clsData.tier;
        const bst = bstOf(clsData);

        let tdHTML = `
            <td>
                <div class="class-td-name" onclick="selectClassForSimulator('${clsName}')">${clsName}</div>
                <div class="class-td-path">${clsData.class_path}</div>
            </td>
            <td><span class="max-lv-badge ${badgeClass}">${clsData.final_level}</span></td>
            <td style="font-weight: 700; color: #fbbf24;">${bst.toFixed(1)}</td>
        `;

        STATS.forEach(s => {
            const statVal = clsData.stats[s];
            const capVal = classCaps[s];
            const isCapped = atCap(statVal, capVal);

            tdHTML += `
                <td class="${isCapped ? 'cap-cell' : ''}">
                    ${statVal.toFixed(1)}
                    ${isCapped ? '<span style="font-size:0.6rem; vertical-align:middle; margin-left:2px;">★</span>' : ''}
                </td>
            `;
        });

        tr.innerHTML = tdHTML;
        tbody.appendChild(tr);
    });

    // 4. Update column sort icons in table header
    updateTableHeaderIcons();
}

// --- Visual SVG Chart ---
function toggleChartStat(s) {
    const chk = document.getElementById(`chk-${s}`);
    if (!chk) return;
    checkedChartStats[s] = chk.checked;
    const el = document.getElementById(`lbl-chk-${s}`);
    if (el) {
        if (checkedChartStats[s]) {
            el.classList.add("checked");
        } else {
            el.classList.remove("checked");
        }
    }
    renderSVGChart();
}

function renderSVGChart() {
    const svg = document.getElementById("svg-comparison-chart");
    if (!svg) return;
    svg.innerHTML = "";

    const charData = activeStatsData[currentCharacterName];
    if (!charData || !charData.classes) return;

    const tierFilter = document.getElementById("filter-chart-tier") ? document.getElementById("filter-chart-tier").value : "all";
    const allClasses = Object.keys(charData.classes).sort();
    const validClasses = filterClassesByTier(charData, allClasses, tierFilter);

    const activeStats = STATS.filter(s => checkedChartStats[s]);

    if (activeStats.length === 0) {
        svg.setAttribute("viewBox", "0 0 800 160");
        svg.setAttribute("height", "160");
        svg.style.height = "160px";
        svg.innerHTML = `<text x="50%" y="80" text-anchor="middle" fill="var(--text-secondary)" font-size="0.9rem" font-family="'Fira Code', monospace">Select at least one stat above to display the visual chart</text>`;
        return;
    }

    if (validClasses.length === 0) {
        svg.setAttribute("viewBox", "0 0 800 160");
        svg.setAttribute("height", "160");
        svg.style.height = "160px";
        svg.innerHTML = `<text x="50%" y="80" text-anchor="middle" fill="var(--text-secondary)" font-size="0.9rem" font-family="'Fira Code', monospace">No classes found for the selected tier filter</text>`;
        return;
    }

    // Dynamic left margin based on the longest class name to prevent label clipping
    const maxLabelLen = Math.max(16, ...validClasses.map(c => c.length));
    const leftMargin = Math.max(200, Math.min(275, maxLabelLen * 9 + 30));

    const containerWidth = svg.parentElement ? svg.parentElement.clientWidth - 48 : 800;
    const svgWidth = Math.max(780, containerWidth);
    const margin = { top: 40, right: 65, bottom: 65, left: leftMargin };
    const chartWidth = svgWidth - margin.left - margin.right;

    // Dynamic maxVal scale (defaults to 60, dynamically expands if any stat exceeds 60)
    let maxVal = 60;
    validClasses.forEach(clsName => {
        const clsData = charData.classes[clsName];
        if (clsData && clsData.stats) {
            activeStats.forEach(s => {
                if (clsData.stats[s] > maxVal) {
                    maxVal = Math.ceil(clsData.stats[s] / 10) * 10;
                }
            });
        }
    });

    const x = (val) => (Math.max(0, val) / maxVal) * chartWidth;

    // Dynamic comfortable height based on number of active stats and classes
    const numClasses = validClasses.length;
    const subBarHeight = 16;
    const statGap = 4;
    const classPaddingTop = 14;
    const classPaddingBottom = 14;
    const rowHeight = (activeStats.length * (subBarHeight + statGap)) - statGap + classPaddingTop + classPaddingBottom;
    const chartHeight = numClasses * rowHeight;
    const totalHeight = margin.top + chartHeight + margin.bottom;

    svg.setAttribute("width", "100%");
    svg.setAttribute("height", totalHeight);
    svg.setAttribute("viewBox", `0 0 ${svgWidth} ${totalHeight}`);
    svg.style.height = `${totalHeight}px`;
    svg.style.minHeight = `${totalHeight}px`;

    let svgContent = "";

    // 1. Gridlines and scale numbers
    const step = maxVal > 60 ? 10 : (maxVal <= 40 ? 5 : 10);
    for (let i = 0; i <= maxVal; i += step) {
        const xPos = margin.left + x(i);
        const isZero = i === 0;
        svgContent += `
            <line x1="${xPos}" y1="${margin.top}" x2="${xPos}" y2="${margin.top + chartHeight}" stroke="rgba(255,255,255,${isZero ? '0.2' : '0.07'})" stroke-dasharray="${isZero ? '0' : '3 3'}" stroke-width="${isZero ? '1.5' : '1'}" />
            <text x="${xPos}" y="${margin.top - 12}" text-anchor="middle" fill="var(--text-secondary)" font-size="0.75rem" font-family="'Fira Code', monospace">${i}</text>
            <text x="${xPos}" y="${margin.top + chartHeight + 20}" text-anchor="middle" fill="var(--text-secondary)" font-size="0.75rem" font-family="'Fira Code', monospace">${i}</text>
        `;
    }

    // 2. Class Rows and Stat Bars
    validClasses.forEach((clsName, idx) => {
        const clsData = charData.classes[clsName];
        const classCaps = capsOf(clsData);
        const yPos = margin.top + (idx * rowHeight);
        const isDefault = clsName === charData.default_class || clsName === charData.direct;

        // Subtle row background or highlight for default class
        const rowBg = isDefault ? 'rgba(157, 78, 221, 0.08)' : (idx % 2 === 1 ? 'rgba(255, 255, 255, 0.015)' : 'transparent');
        svgContent += `<rect x="0" y="${yPos}" width="${svgWidth}" height="${rowHeight}" fill="${rowBg}" />`;

        // Class Name and Subtitle
        const centerY = yPos + (rowHeight / 2);
        const nameColor = isDefault ? 'var(--accent-primary)' : 'var(--text-primary)';
        svgContent += `
            <text x="${margin.left - 14}" y="${centerY - (clsData.final_level ? 6 : 0)}" text-anchor="end" dominant-baseline="middle" fill="${nameColor}" font-size="0.85rem" font-weight="600" font-family="'Fira Code', monospace">${clsName}</text>
        `;
        if (clsData.final_level) {
            svgContent += `
                <text x="${margin.left - 14}" y="${centerY + 10}" text-anchor="end" dominant-baseline="middle" fill="var(--text-secondary)" font-size="0.68rem" font-family="'Fira Code', monospace">${clsData.final_level}${isDefault ? ' (Default)' : ''}</text>
            `;
        }

        // Render each selected stat
        activeStats.forEach((s, sIdx) => {
            const val = (clsData.stats && clsData.stats[s] !== undefined) ? clsData.stats[s] : 0;
            const capVal = (classCaps && classCaps[s] !== undefined) ? classCaps[s] : 99;
            const isCapped = atCap(val, capVal);
            const color = STAT_COLORS[s] || `var(--stat-${s.toLowerCase()})`;
            const barW = Math.max(2, x(val));
            const subY = yPos + classPaddingTop + (sIdx * (subBarHeight + statGap));

            // Track background bar
            svgContent += `<rect x="${margin.left}" y="${subY}" width="${chartWidth}" height="${subBarHeight}" fill="rgba(255,255,255,0.03)" rx="2" />`;

            // Filled Stat Bar
            svgContent += `
                <rect x="${margin.left}" y="${subY}" width="${barW}" height="${subBarHeight}" fill="${color}" fill-opacity="0.92" rx="2">
                    <title>${clsName} - ${s}: ${val.toFixed(1)} ${isCapped ? '(CAPPED at ' + capVal + ')' : '(Cap: ' + capVal + ')'}</title>
                </rect>
            `;

            // Cap line marker
            if (capVal <= maxVal) {
                const capX = margin.left + x(capVal);
                svgContent += `<line x1="${capX}" y1="${subY - 1}" x2="${capX}" y2="${subY + subBarHeight + 1}" stroke="${isCapped ? '#fbbf24' : 'rgba(255,255,255,0.25)'}" stroke-width="2" />`;
            }

            // Stat text label on bar (if wide enough) or before
            if (barW >= 32) {
                svgContent += `<text x="${margin.left + 6}" y="${subY + (subBarHeight / 2) + 4}" fill="#000000" font-size="0.65rem" font-weight="700" font-family="'Fira Code', monospace">${s}</text>`;
            } else {
                svgContent += `<text x="${margin.left - 4}" y="${subY + (subBarHeight / 2) + 4}" text-anchor="end" fill="${color}" font-size="0.65rem" font-weight="600" font-family="'Fira Code', monospace">${s}</text>`;
            }

            // Stat value text at the right edge
            svgContent += `
                <text x="${margin.left + barW + 6}" y="${subY + (subBarHeight / 2) + 4}" fill="${isCapped ? '#fbbf24' : 'var(--text-primary)'}" font-size="0.72rem" font-weight="600" font-family="'Fira Code', monospace">${val.toFixed(1)}${isCapped ? ' ★' : ''}</text>
            `;
        });

        // Bottom row separator
        svgContent += `<line x1="16" y1="${yPos + rowHeight}" x2="${svgWidth - 16}" y2="${yPos + rowHeight}" stroke="var(--border-color)" stroke-opacity="0.4" />`;
    });

    // 3. Legend at the bottom
    const legendY = margin.top + chartHeight + 42;
    let legendX = margin.left;
    let legendHTML = `<g class="chart-legend">`;
    activeStats.forEach(s => {
        const color = STAT_COLORS[s] || `var(--stat-${s.toLowerCase()})`;
        legendHTML += `
            <rect x="${legendX}" y="${legendY - 9}" width="10" height="10" fill="${color}" rx="2" />
            <text x="${legendX + 14}" y="${legendY}" fill="var(--text-primary)" font-size="0.75rem" font-weight="600" font-family="'Fira Code', monospace">${s}</text>
        `;
        legendX += 65;
    });
    legendHTML += `<text x="${legendX + 10}" y="${legendY}" fill="#fbbf24" font-size="0.72rem" font-family="'Fira Code', monospace">★ / | = Cap</text>`;
    legendHTML += `</g>`;
    svgContent += legendHTML;

    svg.innerHTML = svgContent;
}

// --- Simulator System ---
function initSimulator(charName) {
    const charData = activeStatsData[charName];
    const container = document.getElementById("sim-class-list-container");
    container.innerHTML = "";

    const validClasses = Object.keys(charData.classes).sort();

    // Auto-select first class
    selectedSimClass = validClasses.includes("Falcon Knight") ? "Falcon Knight" : (validClasses.includes("Paladin") ? "Paladin" : validClasses[0]);

    validClasses.forEach(cls => {
        const isDefault = cls === charData.default_class || (charData.default_class === "Pegasus Knight" && cls === "Falcon Knight");
        const item = document.createElement("div");
        item.className = `sim-class-item ${cls === selectedSimClass ? 'active' : ''}`;
        item.id = `sim-cls-item-${cls}`;
        item.onclick = () => selectClassForSimulator(cls);

        item.innerHTML = `
            <span>${cls}</span>
            <span style="font-size:0.7rem; opacity:0.6;">${isDefault ? 'Default' : ''}</span>
        `;
        container.appendChild(item);
    });

    runSimulatorSimulation();
}

function selectClassForSimulator(clsName) {
    selectedSimClass = clsName;
    document.querySelectorAll(".sim-class-item").forEach(item => item.classList.remove("active"));
    const el = document.getElementById(`sim-cls-item-${clsName}`);
    if (el) el.classList.add("active");

    // Switch tabs if selected from the table view
    const tabBtn = document.querySelector(".tabs-container button:nth-child(3)");
    switchTab('simulator-view', tabBtn);

    runSimulatorSimulation();
}

function runSimulatorSimulation() {
    const classData = activeStatsData[currentCharacterName].classes[selectedSimClass];
    const arrow = text => text.replaceAll("->", "➔");

    document.getElementById("sim-log-title").innerText = `Level-up Growth Log: ${currentCharacterName} as ${selectedSimClass}`;
    document.getElementById("sim-log-desc").innerText = `Calculated Path: ${arrow(classData.class_path)} (Final Max Level: ${arrow(classData.final_level)})`;

    const tbody = document.getElementById("sim-table-body");
    tbody.innerHTML = "";

    const addRow = (level, clsName, cells, rowClass = "") => {
        const tr = document.createElement("tr");
        tr.className = rowClass;
        tr.innerHTML = `<td>${level}</td><td>${clsName}</td>${cells.join("")}`;
        tbody.appendChild(tr);
    };

    // Replay each class stage. Values are whole hundredths of a point, so the arithmetic is exact.
    let previous = null;
    classData.segs.forEach(([clsName, labelPrefix, firstLevel, rows, start, growths, caps]) => {
        let stats = start;
        if (previous) {
            const gains = stats.map((v, i) => (v - previous[i]) / 100);
            addRow("Promotion", clsName, gains.map(g => `<td style="font-weight:700;">${g >= 0 ? "+" : ""}${g}</td>`), "promo-row");
        }
        for (let row = 0; row < rows; row++) {
            if (row > 0) stats = stats.map((v, i) => Math.min(caps[i] * 100, v + growths[i]));
            addRow(`${labelPrefix}${firstLevel + row}`, clsName, stats.map((v, i) => `
                <td class="${atCap(v, caps[i] * 100) ? 'cap-cell' : ''}">
                    ${(v / 100).toFixed(2)}
                    ${atCap(v, caps[i] * 100) ? '<span class="sim-cap-badge">CAP</span>' : ''}
                </td>
            `));
        }
        previous = stats;
    });
}
