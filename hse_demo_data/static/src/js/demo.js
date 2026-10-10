/* Native links/forms remain usable without JavaScript. No backend mutations. */
(function () {
    "use strict";
    const main = document.querySelector("#main");
    if (!main) return;
    const cards = Array.from(document.querySelectorAll(".module-card"));
    const search = document.querySelector("#module-search");
    const category = document.querySelector("#category-filter");
    const resultCount = document.querySelector("[data-result-count]");
    const empty = document.querySelector("[data-empty-results]");

    function filterModules() {
        const query = search.value.trim().toLocaleLowerCase();
        const group = category.value;
        let shown = 0;
        cards.forEach((card) => {
            const visible = (group === "all" || card.dataset.category === group) &&
                card.dataset.search.includes(query);
            card.hidden = !visible;
            if (visible) shown += 1;
        });
        resultCount.textContent = `Showing ${shown} of ${cards.length} module areas`;
        empty.hidden = shown > 0;
    }
    search.addEventListener("input", filterModules);
    category.addEventListener("change", filterModules);
    document.querySelectorAll("[data-clear-search]").forEach((button) => {
        button.addEventListener("click", () => {
            search.value = "";
            category.value = "all";
            filterModules();
            search.focus();
        });
    });

    const notes = document.querySelector("[data-notes]");
    notes.addEventListener("click", () => {
        const enabled = document.body.classList.toggle("show-notes");
        notes.setAttribute("aria-pressed", String(enabled));
    });
    document.querySelector("[data-start]").addEventListener("click", () => {
        document.querySelector(".journey-card").open = true;
    });

    // This is explicitly a personal presentation checklist, not a record status.
    const storageKey = "hse-demo-checklist:" + main.dataset.seedDate;
    const checks = Array.from(document.querySelectorAll("[data-step]"));
    let demonstrated = {};
    try {
        const saved = JSON.parse(sessionStorage.getItem(storageKey) || "{}");
        if (saved && typeof saved === "object" && !Array.isArray(saved)) demonstrated = saved;
    } catch (_) { /* Storage can be disabled in a private browser. */ }
    checks.forEach((check) => { check.checked = demonstrated[check.dataset.step] === true; });

    function updateProgress() {
        let complete = 0;
        document.querySelectorAll(".journey-card").forEach((journey) => {
            const all = Array.from(journey.querySelectorAll("[data-step]"));
            const count = all.filter((check) => check.checked).length;
            const done = all.length > 0 && count === all.length;
            journey.classList.toggle("complete", done);
            if (done) complete += 1;
            journey.querySelector("[data-progress-for]").textContent = `${count} / ${all.length} shown`;
        });
        document.querySelector("[data-tour-progress]").textContent = `${complete} of 8 journeys demonstrated`;
    }
    checks.forEach((check) => {
        check.addEventListener("change", () => {
            demonstrated[check.dataset.step] = check.checked;
            try { sessionStorage.setItem(storageKey, JSON.stringify(demonstrated)); } catch (_) { /* Optional. */ }
            updateProgress();
        });
    });
    document.querySelector("[data-reset-tour]").addEventListener("click", () => {
        demonstrated = {};
        checks.forEach((check) => { check.checked = false; });
        try { sessionStorage.removeItem(storageKey); } catch (_) { /* Optional. */ }
        updateProgress();
    });
    updateProgress();

    // Open all journey notes for printing and restore the screen afterwards.
    const printable = Array.from(document.querySelectorAll("details"));
    let beforePrint = [];
    window.addEventListener("beforeprint", () => {
        beforePrint = printable.map((detail) => detail.open);
        printable.forEach((detail) => { detail.open = true; });
    });
    window.addEventListener("afterprint", () => {
        printable.forEach((detail, index) => { detail.open = beforePrint[index] || false; });
    });
    document.querySelector("[data-print]").addEventListener("click", () => window.print());

    if ("IntersectionObserver" in window) {
        const sections = Array.from(document.querySelectorAll("main > section"));
        const nav = Array.from(document.querySelectorAll("[data-nav]"));
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                nav.forEach((item) => {
                    const active = item.dataset.nav === entry.target.id;
                    item.classList.toggle("active", active);
                    if (active) item.setAttribute("aria-current", "location");
                    else item.removeAttribute("aria-current");
                });
            });
        }, { rootMargin: "-75px 0px -65% 0px", threshold: 0 });
        sections.forEach((section) => observer.observe(section));
    }
})();
