/** @odoo-module **/

import { Component, onMounted, onPatched } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { FormRenderer } from "@web/views/form/form_renderer";
import { patch } from "@web/core/utils/patch";

/* -------------------------------------------------------------------------
 * HSE Smart Counter — animated, dynamic numeric KPI chip for form views.
 * Renders an integer/float with count-up animation and thousand grouping.
 * ---------------------------------------------------------------------- */
export class HseSmartCounter extends Component {
    static template = "hse.SmartCounter";
    static props = { ...standardFieldProps };

    setup() {
        this.animated = null;
        onMounted(() => this.animateTo(this.rawValue));
        onPatched(() => this.animateTo(this.rawValue));
    }

    get rawValue() {
        const v = this.props.record.data[this.props.name];
        return typeof v === "number" ? v : (parseFloat(v) || 0);
    }

    animateTo(target) {
        if (this.animated === target) return;
        this.animated = target;
        const el = this.el?.querySelector(".hse-smart-counter");
        if (!el) return;
        const from = parseFloat(el.dataset.v || "0");
        const start = performance.now();
        const dur = 450;
        const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });
        const step = (now) => {
            const t = Math.min((now - start) / dur, 1);
            const eased = 1 - Math.pow(1 - t, 3);
            const val = from + (target - from) * eased;
            el.textContent = fmt.format(t < 1 ? Math.round(val * 10) / 10 : target);
            el.dataset.v = target;
            if (t < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
    }

    get display() {
        return new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(this.rawValue);
    }
}

registry.category("fields").add("hse_smart_counter", {
    component: HseSmartCounter,
    supportedTypes: ["integer", "float"],
});

/* -------------------------------------------------------------------------
 * HSE Relative Date — humanized dynamic date badge ("3d ago", "in 12d").
 * Overdue = red, imminent (<= 7d) = amber, future = slate.
 * ---------------------------------------------------------------------- */
export class HseRelativeDate extends Component {
    static template = "hse.RelativeDateBadge";
    static props = { ...standardFieldProps };

    get info() {
        const v = this.props.record.data[this.props.name];
        if (!v) return null;
        const d = typeof v.toJSDate === "function" ? v.toJSDate() : new Date(v);
        if (isNaN(d.getTime())) return null;
        const days = Math.round((d.getTime() - Date.now()) / 86400000);
        const exact = d.toISOString().slice(0, 10);
        let label, cls;
        if (days === 0) { label = "today"; cls = "hse-rel-soon"; }
        else if (days === 1) { label = "tomorrow"; cls = "hse-rel-soon"; }
        else if (days === -1) { label = "yesterday"; cls = "hse-rel-overdue"; }
        else if (days < 0) { label = Math.abs(days) + "d ago"; cls = "hse-rel-overdue"; }
        else if (days <= 7) { label = "in " + days + "d"; cls = "hse-rel-soon"; }
        else { label = "in " + days + "d"; cls = "hse-rel-ok"; }
        return { label, cls, exact };
    }
}

registry.category("fields").add("hse_relative_date", {
    component: HseRelativeDate,
    supportedTypes: ["date", "datetime"],
});

/* -------------------------------------------------------------------------
 * Form Renderer enhancement — client-side polish applied to every backend
 * form view: hero entrance animation, staggered KPI pop-in, modern sheet
 * card and semantic (dynamic) colorization of hero state badges.
 * ---------------------------------------------------------------------- */
const HSE_BADGE_COLORS = [
    ["reject", ["#fef2f2", "#dc2626", "#b91c1c"]],
    ["cancel", ["#fef2f2", "#dc2626", "#b91c1c"]],
    ["expired", ["#fef2f2", "#dc2626", "#b91c1c"]],
    ["critical", ["#fef2f2", "#dc2626", "#b91c1c"]],
    ["non_compliant", ["#fef2f2", "#dc2626", "#b91c1c"]],
    ["overdue", ["#fef2f2", "#dc2626", "#b91c1c"]],
    ["approved", ["#f0fdf4", "#16a34a", "#15803d"]],
    ["completed", ["#f0fdf4", "#16a34a", "#15803d"]],
    ["compliant", ["#f0fdf4", "#16a34a", "#15803d"]],
    ["closed", ["#f0fdf4", "#16a34a", "#15803d"]],
    ["done", ["#f0fdf4", "#16a34a", "#15803d"]],
    ["active", ["#f0fdf4", "#16a34a", "#15803d"]],
    ["published", ["#f0fdf4", "#16a34a", "#15803d"]],
    ["verified", ["#f0fdf4", "#16a34a", "#15803d"]],
    ["effective", ["#f0fdf4", "#16a34a", "#15803d"]],
    ["progress", ["#eff6ff", "#2563eb", "#1d4ed8"]],
    ["assigned", ["#eff6ff", "#2563eb", "#1d4ed8"]],
    ["open", ["#eff6ff", "#2563eb", "#1d4ed8"]],
    ["review", ["#fffbeb", "#d97706", "#b45309"]],
    ["pending", ["#fffbeb", "#d97706", "#b45309"]],
    ["expiring", ["#fffbeb", "#d97706", "#b45309"]],
    ["partial", ["#fffbeb", "#d97706", "#b45309"]],
    ["locked", ["#f5f3ff", "#7c3aed", "#6d28d9"]],
];

function hseBadgeTheme(text) {
    const t = (text || "").toLowerCase();
    for (const [key, colors] of HSE_BADGE_COLORS) {
        if (t.includes(key)) return colors;
    }
    return ["#f1f5f9", "#475569", "#334155"]; // neutral slate
}

patch(FormRenderer.prototype, {
    setup() {
        super.setup();
        onMounted(() => this._hseEnhance());
        onPatched(() => this._hseEnhance());
    },

    _hseEnhance() {
        const root = this.el;
        if (!root) return;

        // Modern card treatment for the form sheet
        const sheet = root.querySelector(".o_form_sheet");
        if (sheet && !sheet.classList.contains("hse-modern")) {
            sheet.classList.add("hse-modern");
        }

        // Hero entrance animation + staggered chips/KPIs (once per mount)
        const hero = root.querySelector(".hse-x-hero");
        if (hero && !hero.classList.contains("hse-anim-in")) {
            hero.classList.add("hse-anim-in");
            hero.querySelectorAll(".hse-x-kpi, .hse-x-chip, .hse-x-badge").forEach((el, i) => {
                el.style.animationDelay = (90 + i * 70) + "ms";
                el.classList.add("hse-pop-in");
            });
        }

        // Dynamic semantic colorization of the hero state badge
        root.querySelectorAll(".hse-x-badge .o_badge_text").forEach((el) => {
            if (el.dataset.hseThemed) return;
            const [bg, border, fg] = hseBadgeTheme(el.textContent);
            el.style.background = bg;
            el.style.border = "1px solid " + border;
            el.style.color = fg;
            el.dataset.hseThemed = "1";
        });
    },
});
