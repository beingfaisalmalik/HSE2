// Read-only, authenticated browser checks against an explicitly isolated demo.
// Credentials come from the environment, not from source control or URLs.
import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";
import { chromium } from "playwright-core";

const base = (process.env.DEMO_BASE_URL || "http://127.0.0.1:8069").replace(/\/$/, "");
const artifacts = resolve(process.env.DEMO_ARTIFACT_DIR || ".demo-runtime/browser");
const presenterPassword = process.env.DEMO_PRESENTER_PASSWORD;
const portalPassword = process.env.DEMO_PORTAL_PASSWORD;
assert(presenterPassword && portalPassword, "Export the private demo passwords before running browser checks.");
await mkdir(artifacts, { recursive: true });
const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.DEMO_CHROMIUM_PATH || undefined,
    args: JSON.parse(process.env.DEMO_CHROMIUM_ARGS || "[]"),
});
const errors = [];
function watch(page) {
    page.on("pageerror", error => errors.push(error.message));
}
async function login(page, username, password, target) {
    await page.goto(`${base}/web/login?redirect=${encodeURIComponent(target)}`);
    await page.locator('input[name="login"]').fill(username);
    await page.locator('input[name="password"]').fill(password);
    await page.getByRole("button", { name: "Log in", exact: true }).click();
    await page.waitForURL(`${base}${target}`);
}
async function screenshot(page, name) {
    await page.screenshot({ path: resolve(artifacts, name) });
}

try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1050 } });
    const page = await context.newPage();
    watch(page);
    await page.goto(`${base}/hse/demo/welcome`);
    assert(await page.getByText("Your client demo starts here.", { exact: true }).isVisible());
    assert.equal(await page.locator(".module-card, .kpi-card").count(), 0);
    await screenshot(page, "01-welcome.png");
    await login(page, "hse.presenter", presenterPassword, "/hse/demo");
    assert.equal(await page.locator(".module-card").count(), 73);
    await screenshot(page, "02-demo-hub.png");
    const samples = await page.locator(".module-card").evaluateAll(cards => cards.map(card => ({
        title: card.querySelector("h3").textContent.trim(),
        url: card.querySelector(".module-links a:last-child").getAttribute("href"),
    })));
    const reports = await page.locator(".report-links a").evaluateAll(links => links
        .map(link => link.getAttribute("href")).filter(url => url.startsWith("/report/html/")));
    const dashboard = await page.locator(".toolkit-nav a").first().getAttribute("href");
    await page.locator("#module-search").fill("confined");
    assert.equal(await page.locator(".module-card:visible").count(), 1);
    await page.locator("#module-search").fill("keyword-with-no-matching-module");
    assert(await page.locator("[data-empty-results]").isVisible());
    await page.locator(".explorer-toolbar [data-clear-search]").click();
    await page.locator("#category-filter").selectOption("environment");
    assert.equal(await page.locator(".module-card:visible").count(), 6);
    await page.locator("#category-filter").selectOption("all");
    await page.locator("[data-start]").click();
    assert.equal(await page.locator(".journey-card[open]").count(), 1);
    await page.locator("[data-notes]").click();
    assert(await page.locator(".journey-card[open] .presenter-note").first().isVisible());
    await page.locator('[data-step="incident-0"]').check();
    await page.reload();
    assert(await page.locator('[data-step="incident-0"]').isChecked());
    await page.locator("[data-reset-tour]").click();
    assert(!(await page.locator('[data-step="incident-0"]').isChecked()));
    await page.setViewportSize({ width: 390, height: 844 });
    await screenshot(page, "03-demo-mobile.png");
    const overflow = await page.evaluate(() => ({
        width: document.documentElement.scrollWidth,
        viewport: window.innerWidth,
        elements: Array.from(document.querySelectorAll("main *")).filter(element =>
            element.getBoundingClientRect().right > window.innerWidth + 1).slice(0, 8)
            .map(element => element.className || element.tagName),
    }));
    assert(overflow.width <= overflow.viewport, `Mobile overflow: ${JSON.stringify(overflow)}`);
    await page.setViewportSize({ width: 1440, height: 1050 });
    // Browser PDF checks the printable walkthrough only. It is NOT a test of
    // Odoo's native wkhtmltopdf-based report exporter.
    await page.pdf({ path: resolve(artifacts, "walkthrough-browser-print.pdf"), format: "A4", printBackground: true });
    for (const sample of samples) {
        const query = new URLSearchParams(sample.url.split("#")[1]);
        const model = query.get("model");
        const id = Number(query.get("id"));
        const reading = page.waitForResponse(response => response.url().includes(`/${model}/web_read`), { timeout: 60000 });
        await page.goto(base + sample.url);
        const data = await (await reading).json();
        assert(!data.error, `${sample.title}: ${data.error?.message}`);
        assert.equal(data.result[0].id, id);
        await page.waitForSelector(".o_form_view", { timeout: 60000 });
        // Allow the Owl render and its attached field widgets to complete.
        await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        if (["incident.reporting", "hse.cse.permit", "hse.hazop.study"].includes(model)) {
            await screenshot(page, `form-${model}.png`);
        }
        console.log(`FORM OK ${sample.title}`);
    }
    const collecting = page.waitForResponse(response => response.url().includes("/hse/dashboard/data"));
    await page.goto(base + dashboard);
    const kpis = await (await collecting).json();
    assert.equal(kpis.matrix_grid.flat().length, 25);
    assert(kpis.total_incidents > 0);
    await page.waitForSelector(".o_hse_dashboard");
    await screenshot(page, "04-executive-dashboard.png");
    for (const path of reports) {
        const response = await context.request.get(base + path);
        assert.equal(response.status(), 200, path);
        assert((await response.body()).length > 500, path);
    }
    assert.equal(reports.length, 10);
    const guide = await context.request.get(`${base}/hse/demo/guide`);
    assert.equal(guide.status(), 200);
    assert((await guide.text()).includes("PSSR"));
    const coverage = await context.request.get(`${base}/hse/demo/coverage.csv`);
    assert.equal(coverage.status(), 200);
    const contractorContext = await browser.newContext({ viewport: { width: 1440, height: 1050 } });
    const contractorPage = await contractorContext.newPage();
    watch(contractorPage);
    await login(contractorPage, "hse.contractor", portalPassword, "/hse/portal");
    await contractorPage.goto(`${base}/hse/portal/my-submissions`);
    await screenshot(contractorPage, "05-contractor-submissions.png");
    assert(await contractorPage.locator(".hp-main").filter({
        hasText: "Air hose crosses the marked route to Muster Alpha.",
    }).isVisible());
    for (const path of ["/hse/demo", "/hse/demo/guide", "/hse/demo/coverage.csv"]) {
        assert.equal((await contractorContext.request.get(base + path)).status(), 403, path);
    }
    assert.deepEqual(errors, [], "Unexpected browser JavaScript errors");
    console.log(`PASS: ${samples.length} native forms, ten HTML reports, dashboard, filtering, checklist, mobile, printing and role isolation.`);
    console.log(`Artifacts: ${artifacts}`);
} finally {
    await browser.close();
}
