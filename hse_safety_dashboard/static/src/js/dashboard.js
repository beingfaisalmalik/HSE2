/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, useRef, useEffect } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/**
 * Format a number like the Excel workbook: #,##0 for counts, 0.00 for rates.
 */
function fmtCount(v) {
    if (v === null || v === undefined) { return "n/a"; }
    return Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 });
}
function fmtRate(v) {
    if (v === null || v === undefined) { return "n/a"; }
    return Number(v).toFixed(2);
}
function fmtPct(v) {
    if (v === null || v === undefined) { return "n/a"; }
    return Math.round(v * 100) + "%";
}
function fmtNum(v) {
    if (v === null || v === undefined) { return "n/a"; }
    return Number(v).toLocaleString();
}

/**
 * Month-over-month delta string — same semantics as the Excel cards:
 * "▲ +N vs Aug-26" / "▼ -N vs Aug-26" / "● same as Aug-26" / "– no comparison"
 * `invertGood`: True when a *decrease* is good (injuries, overdue CAs).
 */
function delta(cur, prev, prevLabel, { fmt = fmtCount, invertGood = false, warnZeroHours = false } = {}) {
    if (warnZeroHours && (!cur || cur === 0)) {
        return { text: "⚠ Enter hours in Monthly Figures", cls: "hse-delta-warn" };
    }
    if (prev === null || prev === undefined || cur === null || cur === undefined) {
        return { text: "– no comparison", cls: "hse-delta-none" };
    }
    if (cur === prev) {
        return { text: `● same as ${prevLabel}`, cls: "hse-delta-same" };
    }
    const up = cur > prev;
    const diff = Math.abs(cur - prev);
    const sign = up ? "+" : "-";
    let cls;
    if (invertGood) {
        cls = up ? "hse-delta-bad" : "hse-delta-good";
    } else {
        cls = up ? "hse-delta-good" : "hse-delta-bad";
    }
    // Rates show 2 decimals, counts integers
    const diffTxt = fmt === fmtRate ? Math.abs(diff).toFixed(2) : fmtCount(Math.abs(diff));
    return { text: `${up ? "▲" : "▼"} ${sign}${diffTxt} vs ${prevLabel}`, cls };
}

export class HseSafetyDashboard extends Component {
    setup() {
        this.state = useState({
            mode: this.props.action.context?.default_mode === "yearly" ? "yearly" : "monthly",
            year: null,
            years: [],
            monthNo: null,
            months: [],
            data: null,
            loading: true,
            showHealth: false,
        });
        this.orm = useService("orm");
        this.action = useService("action");
        this.trendChartRef = useRef("trendChart");
        onWillStart(async () => {
            await this.loadSettings();
            await this.loadDashboard();
        });
        useEffect(() => {
            this.renderChart();
            return () => {
                if (this._chart) {
                    this._chart.destroy();
                    this._chart = null;
                }
            };
        }, () => [this.state.data, this.state.mode]);
    }

    async loadSettings() {
        const settings = await this.orm.call(
            "hse.safety.settings", "get_settings", [], {});
        this.state.year = settings.reporting_year;
    }

    async loadDashboard() {
        this.state.loading = true;
        const data = await this.orm.call(
            "hse.kpi.engine", "get_dashboard", [], 
            { year: this.state.year, month_no: this.state.monthNo || undefined });
        this.state.data = data;
        this.state.year = data.year;
        // Dynamic options straight from the data — nothing hardcoded
        this.state.years = (data.years || []).map((y) => ({ no: y, label: String(y) }));
        this.state.monthNo = data.month_no;
        const labelByNo = {};
        for (const m of data.months) { labelByNo[m.month_no] = m.label; }
        this.state.months = (data.available_months || []).map((no) => ({
            no, label: labelByNo[no] || String(no),
        }));
        this.state.loading = false;
    }

    async onYearChange(ev) {
        this.state.year = parseInt(ev.target.value, 10);
        // Let the engine pick the best month for the new year (current
        // month when it holds data, otherwise the latest month with data).
        this.state.monthNo = null;
        await this.loadDashboard();
    }

    async onMonthChange(ev) {
        this.state.monthNo = parseInt(ev.target.value, 10);
        await this.loadDashboard();
    }

    onModeChange(mode) {
        this.state.mode = mode;
    }

    toggleHealth() {
        this.state.showHealth = !this.state.showHealth;
    }

    // ------------------------------------------------------------------
    // KPI card helpers (mirror the Excel Dashboard cards exactly)
    // ------------------------------------------------------------------
    get d() { return this.state.data; }
    get stats() { return this.d.stats; }
    get prev() { return this.d.prior; }
    get ytd() { return this.d.ytd_to_month; }
    get prevLabel() { return this.d.prev_label || _t("(no prior month)"); }

    card(label, cur, prevVal, ytdVal, opts = {}) {
        const fmt = opts.fmt || fmtCount;
        return {
            label,
            value: opts.valueText !== undefined ? opts.valueText : fmt(cur),
            delta: delta(cur, prevVal, this.prevLabel, opts),
            ytd: opts.ytdText !== undefined ? opts.ytdText
                : (opts.showYtd === false ? null
                   : `${_t("YTD")}: ${ytdVal !== undefined ? fmt(ytdVal) : fmt(cur)}`),
            cls: opts.cls || "",
        };
    }

    get cardsInjury() {
        const s = this.stats, p = this.prev, y = this.ytd, d = this.d;
        const dsl = d.days_since_lti;
        return [
            this.card(_t("Lost Time Injuries (LTI)"), s.lti, p?.lti, y.lti, { invertGood: true }),
            this.card(_t("Recordable Cases (LTI + MTC)"), s.recordable, p?.recordable, y.recordable, { invertGood: true }),
            this.card(_t("Medical Treatment Cases"), s.mtc, p?.mtc, y.mtc, { invertGood: true }),
            this.card(_t("First Aid Cases"), s.first_aid, p?.first_aid, y.first_aid, { invertGood: true }),
            this.card(_t("Lost Workdays"), s.lost_workdays, p?.lost_workdays, y.lost_workdays, { invertGood: true }),
            this.card(_t("Days since last LTI"), dsl.days, null, null, {
                valueText: `${dsl.days} day${dsl.days === 1 ? "" : "s"}`,
                ytdText: dsl.has_lti
                    ? `${_t("Last LTI")}: ${dsl.last_date}`
                    : `${_t("No LTI recorded in")} ${d.year}`,
                showYtd: false,
            }),
        ];
    }

    get cardsExposure() {
        const s = this.stats, p = this.prev, y = this.ytd;
        return [
            this.card(_t("Man-Hours Worked"), s.man_hours, p?.man_hours, y.man_hours, {
                fmt: fmtNum, warnZeroHours: !s.man_hours,
                ytdText: `${_t("YTD")}: ${fmtNum(y.man_hours)}`,
            }),
            this.card(_t("LTIFR"), s.ltifr, p?.ltifr, y.ltifr, {
                fmt: fmtRate, valueText: fmtRate(s.ltifr),
                ytdText: `${_t("YTD")}: ${fmtRate(y.ltifr)}`,
            }),
            this.card(_t("TRIR"), s.trir, p?.trir, y.trir, {
                fmt: fmtRate, valueText: fmtRate(s.trir),
                ytdText: `${_t("YTD")}: ${fmtRate(y.trir)}`,
            }),
            this.card(_t("Severity Rate"), s.severity, p?.severity, y.severity, {
                fmt: fmtRate, valueText: fmtRate(s.severity),
                ytdText: `${_t("YTD")}: ${fmtRate(y.severity)}`,
            }),
            this.card(_t("Near Misses"), s.near_misses, p?.near_misses, y.near_misses),
            this.card(_t("Non-Injury Incidents"), s.incidents, p?.incidents, y.incidents, { invertGood: true }),
        ];
    }

    get cardsObs() {
        const s = this.stats, p = this.prev, y = this.ytd;
        return [
            this.card(_t("Unsafe Acts"), s.unsafe_acts, p?.unsafe_acts, y.unsafe_acts, { invertGood: true }),
            this.card(_t("Unsafe Conditions"), s.unsafe_conditions, p?.unsafe_conditions, y.unsafe_conditions, { invertGood: true }),
            this.card(_t("Total Observations"), s.observations, p?.observations, y.observations, {
                ytdText: `${_t("YTD")}: ${fmtCount(y.observations)} · ${_t("Closed")}: ${fmtCount(y.observations_closed)}`,
            }),
            this.card(_t("Open CAs"), s.ca_open, p?.ca_open, y.ca_open, {
                invertGood: true,
                ytdText: `${_t("YTD")}: ${fmtCount(y.ca_open)}`,
            }),
            this.card(_t("CAs Flagged Overdue"), s.ca_overdue, p?.ca_overdue, y.ca_overdue, {
                invertGood: true, ytdText: `${_t("YTD")}: ${fmtCount(y.ca_overdue)}`,
            }),
            this.card(_t("CA Closure Rate"), s.ca_closure_rate, p?.ca_closure_rate, y.ca_closure_rate, {
                fmt: fmtPct, valueText: fmtPct(s.ca_closure_rate),
                ytdText: `${_t("Closed")}: ${fmtCount(y.ca_closed)} of ${fmtCount(y.ca_linked)} ${_t("linked")}`,
            }),
        ];
    }

    get cardsLeading() {
        const s = this.stats, p = this.prev, y = this.ytd;
        const regNote = s.ptw_register_rows === s.ptw_issued
            ? `${_t("Register rows")}: ${fmtCount(s.ptw_register_rows)} ✓`
            : `${_t("Register rows")}: ${fmtCount(s.ptw_register_rows)} ≠ ${_t("entered figure")}`;
        return [
            this.card(_t("Permits to Work Issued"), s.ptw_issued, p?.ptw_issued, y.ptw_issued, {
                ytdText: regNote,
            }),
            this.card(_t("Toolbox Talks"), s.toolbox_talks, p?.toolbox_talks, y.toolbox_talks),
            this.card(_t("Training Hours"), s.training_hours, p?.training_hours, y.training_hours, { fmt: fmtNum }),
            this.card(_t("Inspection Compliance"), s.insp_compliance, p?.insp_compliance, y.insp_compliance, {
                fmt: fmtPct, valueText: fmtPct(s.insp_compliance),
                ytdText: `${_t("Completed")}: ${fmtCount(s.insp_completed)} ${_t("of")} ${fmtCount(s.insp_planned)} ${_t("planned")}`,
            }),
            this.card(_t("Internal Audit Score"), s.audit_score, p?.audit_score, y.audit_score, {
                fmt: fmtRate, valueText: s.audit_score ? fmtRate(s.audit_score) : "n/a",
                ytdText: `${_t("YTD avg")}: ${fmtRate(y.audit_score)}`,
            }),
            this.card(_t("Hot-Work Permits"), s.ptw_hot_work ?? 0, p?.ptw_hot_work ?? 0, y.ptw_hot_work ?? 0, {
                ytdText: `${_t("YTD")}: ${fmtCount(y.ptw_hot_work ?? 0)} ${_t("hot-work permits")}`,
            }),
        ];
    }

    get healthAttention() { return this.d.health_attention; }

    get yearlyCards() {
        const y = this.d.ytd_full;
        return [
            ["Man-hours", y.man_hours.toLocaleString()],
            ["LTI", y.lti],
            ["Recordable", y.recordable],
            ["Lost Workdays", y.lost_workdays],
            ["LTIFR", y.ltifr !== null && y.ltifr !== undefined ? y.ltifr.toFixed(2) : "n/a"],
            ["TRIR", y.trir !== null && y.trir !== undefined ? y.trir.toFixed(2) : "n/a"],
            ["Severity", y.severity !== null && y.severity !== undefined ? y.severity.toFixed(2) : "n/a"],
            ["Days since last LTI", this.d.days_since_lti_year.days],
        ];
    }

    get openRegisters() {
        return this.d.registers;
    }

    onOpenRecord(model, resId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: model,
            res_id: resId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    // ------------------------------------------------------------------
    // Chart.js trend — 12-month observations & injuries (like the Excel chart)
    // ------------------------------------------------------------------
    renderChart() {
        if (this.state.mode !== "monthly" || !this.state.data) { return; }
        const canvas = this.trendChartRef.el;
        if (!canvas) { return; }
        if (this._chart) {
            this._chart.destroy();
            this._chart = null;
        }
        const months = this.d.months;
        const labels = months.map((m) => m.label);
        const obs = months.map((m) => m.observations);
        const injuries = months.map((m) => m.all_injuries);
        const selected = this.d.month_no - 1;
        const bgObs = months.map((_m, i) => i === selected ? "rgba(2,129,168,0.85)" : "rgba(2,129,168,0.35)");
        const bgInj = months.map((_m, i) => i === selected ? "rgba(220,53,69,0.9)" : "rgba(220,53,69,0.4)");
        this._chart = new Chart(canvas, {
            type: "bar",
            data: {
                labels,
                datasets: [
                    { label: _t("Observations"), data: obs, backgroundColor: bgObs },
                    { label: _t("Injuries"), data: injuries, backgroundColor: bgInj },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: "bottom" } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
            },
        });
    }

}

HseSafetyDashboard.template = "hse_safety_dashboard.HseDashboard";

registry.category("actions").add("hse_safety_dashboard.dashboard", HseSafetyDashboard);
