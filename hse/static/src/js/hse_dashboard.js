/** @odoo-module **/

import { Component, useState, onWillStart, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const AUTO_REFRESH_MS = 60000;

export class HSEDashboard extends Component {
    static template = "hse.HSEDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            loadError: false,
            activeTab: "overview",
            autoRefresh: false,
            lastSync: "",
            kpis: {},
            activeBypasses: [],
            activePermits: [],
            overdueActions: [],
            matrixGrid: [],
            simopsList: [],
            recentObservations: [],
            riskMix: [],
        });
        this._timer = null;

        onWillStart(async () => {
            await this.loadData();
            this._startAutoRefresh();
        });
        onWillUnmount(() => this._stopAutoRefresh());
    }

    _startAutoRefresh() {
        this._stopAutoRefresh();
        if (this.state.autoRefresh) {
            this._timer = setInterval(() => this.loadData(true), AUTO_REFRESH_MS);
        }
    }

    _stopAutoRefresh() {
        if (this._timer) {
            clearInterval(this._timer);
            this._timer = null;
        }
    }

    toggleAutoRefresh() {
        this.state.autoRefresh = !this.state.autoRefresh;
        this._startAutoRefresh();
    }

    setTab(tabName) {
        this.state.activeTab = tabName;
    }

    async loadData(silent) {
        if (!silent) {
            this.state.loading = true;
        }
        try {
            // Plain HTTP JSON endpoint: works with fetch, browser address bar,
            // and external monitors. Relative URL -> same origin, proxy-safe.
            const response = await fetch("/hse/dashboard/data", {
                method: "GET",
                headers: { "Accept": "application/json" },
                credentials: "same-origin",
            });
            if (!response.ok) {
                throw new Error("Dashboard endpoint HTTP " + response.status);
            }
            const data = await response.json();
            this.state.kpis = data;
            this.state.activeBypasses = data.active_bypasses_list || [];
            this.state.activePermits = data.active_permits_list || [];
            this.state.overdueActions = data.overdue_actions_list || [];
            this.state.matrixGrid = data.matrix_grid || [];
            this.state.simopsList = data.simops_conflicts_list || [];
            this.state.recentObservations = data.recent_observations || [];
            this.state.lastSync = data.generated_at || new Date().toLocaleString();
            this.state.loadError = false;
            this._computeRiskMix();
        } catch (error) {
            console.error("Error loading HSE Dashboard Data:", error);
            this.state.loadError = true;
        } finally {
            this.state.loading = false;
        }
    }

    /** Dynamic hazard distribution across the 5x5 matrix (derived live). */
    _computeRiskMix() {
        const counts = { low: 0, medium: 0, high: 0, critical: 0 };
        const totals = { low: 0, medium: 0, high: 0, critical: 0 };
        for (const row of this.state.matrixGrid) {
            for (const cell of row) {
                totals[cell.level.toLowerCase()] += 1;
                counts[cell.level.toLowerCase()] += cell.count || 0;
            }
        }
        const total = counts.low + counts.medium + counts.high + counts.critical;
        this.state.riskMix = ["critical", "high", "medium", "low"].map((lvl) => ({
            key: lvl,
            label: lvl.charAt(0).toUpperCase() + lvl.slice(1),
            count: counts[lvl],
            totalCells: totals[lvl],
            pct: total ? Math.round((counts[lvl] / total) * 100) : 0,
        }));
    }

    get barrierHealthColor() {
        const v = this.state.kpis.barrier_health_pct ?? 100;
        if (v >= 90) return "#10b981";
        if (v >= 70) return "#f59e0b";
        return "#ef4444";
    }

    get trirSourceLabel() {
        const map = {
            api_rp_754_metrics: "Live API RP 754 exposure hours",
            config_parameter: "Configured baseline hours",
            default_baseline: "Default baseline (250k h)",
        };
        return map[this.state.kpis.trir_source] || "";
    }

    get ltiCounter() {
        const v = this.state.kpis.days_without_lti;
        return (v === 0 || v) ? v : "—";
    }

    openAction(resModel, actionName) {
        this.action.doAction({
            name: actionName,
            type: "ir.actions.act_window",
            res_model: resModel,
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openRecord(resModel, resId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: resModel,
            res_id: resId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    viewIncidents() {
        this.openAction("incident.reporting", "Incidents");
    }

    viewPermits() {
        this.action.doAction({
            name: "Permits to Work",
            type: "ir.actions.act_window",
            res_model: "hse.permit",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            target: "current",
        });
    }

    viewBypasses() {
        this.openAction("hse.bypass", "Safety Bypasses & Inhibits");
    }

    viewInvestigations() {
        this.openAction("incident.investigation", "Incident Investigations");
    }

    viewActions() {
        this.openAction("hse.action", "HSE Actions (CAPA)");
    }

    viewCertifications() {
        this.openAction("hse.personnel.certification", "Personnel Certifications");
    }

    viewObservations() {
        this.openAction("observation.observation", "Proactive Safety Observations");
    }

    viewLoto() {
        this.openAction("hse.loto.plan", "LOTO Isolation Schemes");
    }

    viewMoc() {
        this.openAction("hse.moc", "Management of Change (MOC)");
    }

    viewSimops() {
        this.action.doAction({
            name: "Active SIMOPS Conflicts",
            type: "ir.actions.act_window",
            res_model: "hse.permit",
            domain: [["has_simops_conflict", "=", true], ["state", "in", ["approved", "active"]]],
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    filterRiskCell(consequence, likelihood) {
        this.action.doAction({
            name: `Hazards (Severity: ${consequence}, Likelihood: ${likelihood})`,
            type: "ir.actions.act_window",
            res_model: "ra_jsa.hazard",
            domain: [["severity_level", "=", consequence.toString()], ["likelihood_level", "=", likelihood.toString()]],
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }
}

registry.category("actions").add("hse_dashboard", HSEDashboard);
