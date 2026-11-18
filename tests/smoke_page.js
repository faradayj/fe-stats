// Drive every game, character, class, tab and filter of app.js against a stub DOM.
const fs = require("fs"), vm = require("vm");
const root = process.argv[2];

const els = {};
const el = () => ({
    value: "all", html: "", innerText: "", className: "", checked: true, children: [],
    get innerHTML() { return this.html; }, set innerHTML(v) { this.html = v; this.children = []; },
    style: { setProperty() {} }, classList: { add() {}, remove() {} },
    appendChild(c) { this.children.push(c); }, addEventListener() {}, setAttribute() {},
    parentElement: { clientWidth: 1000 },
});
const byId = id => (els[id] ||= el());
const document = {
    getElementById: byId, createElement: el, querySelector: () => el(), querySelectorAll: () => [],
    documentElement: el(),
};
let ready;
const ctx = vm.createContext({ document, console, window: { addEventListener(_, fn) { ready = fn; } } });
for (const f of ["average_stats_data.js", "app.js"]) vm.runInContext(fs.readFileSync(`${root}/${f}`, "utf8"), ctx, { filename: f });

byId("search-bar").value = "";
byId("game-selector").value = "fe5";
ready();

ctx.byId = byId;
ctx.el = el;
const report = vm.runInContext(`(() => {
    const out = { games: 0, chars: 0, classes: 0, simRows: 0, promoRows: 0, boards: 0, problems: [] };
    const nums = html => [...html.matchAll(/>\\s*(-?\\d+\\.\\d\\d)\\s/g)].map(m => Number(m[1]));
    for (const game of Object.keys(AVERAGE_STATS_DATA)) {
        switchGame(game);
        out.games++;
        for (const pool of ["all", "special", "cavalry", "magic", "infantry"]) { byId("filter-pool").value = pool; filterSidebarList(); }
        for (const view of ["reclass-list-view", "visual-chart-view", "simulator-view", "bst-leaderboard-view"]) switchTab(view, el());
        for (const cls of Object.keys(bstClassRankings)) {
            for (const col of ["rank", "name", "path", "level", "bst", STATS[1]]) handleBSTHeaderClick(col);
            selectBstClass(cls);
            out.boards++;
            if (!bstClassRankings[cls].length) out.problems.push(game + ": empty leaderboard " + cls);
        }
        for (const [name, charData] of Object.entries(activeStatsData)) {
            loadCharacterDetails(name);
            out.chars++;
            const shown = new Set();
            for (const tier of ["promoted", "base", "special", "all"]) {
                byId("filter-table-tier").value = tier; byId("filter-chart-tier").value = tier;
                renderReclassTable(name); renderSVGChart();
                if (tier !== "all") byId("reclass-table-body").children.forEach(() => shown.add(shown.size));
            }
            if (shown.size !== Object.keys(charData.classes).length) out.problems.push(game + "/" + name + ": tier filters show " + shown.size + " of " + Object.keys(charData.classes).length + " classes");
            for (const col of ["class", "level", "bst", STATS[0]]) handleHeaderClick(col);
            for (const [cls, classData] of Object.entries(charData.classes)) {
                selectedSimClass = cls;
                runSimulatorSimulation();
                out.classes++;
                const rows = byId("sim-table-body").children;
                out.simRows += rows.length;
                out.promoRows += rows.filter(r => r.className === "promo-row").length;
                const last = nums(rows.at(-1).innerHTML);
                const want = STATS.map(s => Number(classData.stats[s].toFixed(2)));
                if (JSON.stringify(last) !== JSON.stringify(want)) out.problems.push(game + "/" + name + "/" + cls + ": simulator ends at " + last + ", table shows " + want);
            }
        }
    }
    return out;
})()`, ctx);
console.log(JSON.stringify({ ...report, problems: report.problems.length }));
report.problems.slice(0, 25).forEach(p => console.log("  " + p));
process.exit(report.problems.length ? 1 : 0);
