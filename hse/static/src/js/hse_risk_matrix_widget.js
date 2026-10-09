/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class HseRiskMatrixWidget extends Component {
    static template = "hse.RiskMatrixWidget";
    static props = {
        ...standardFieldProps,
    };

    setup() {}

    get currentSeverity() {
        // Reads severity_level field from the record
        const val = this.props.record.data.severity_level;
        return parseInt(val) || 1;
    }

    get currentLikelihood() {
        // Reads likelihood_level field from the record
        const val = this.props.record.data.likelihood_level;
        return parseInt(val) || 1;
    }

    get currentScore() {
        return this.currentSeverity * this.currentLikelihood;
    }

    get currentRiskLevel() {
        const score = this.currentScore;
        if (score >= 16) return { name: "Critical Risk", color: "#ef4444", class: "badge-critical" };
        if (score >= 10) return { name: "High Risk", color: "#f97316", class: "badge-high" };
        if (score >= 4) return { name: "Medium Risk", color: "#f59e0b", class: "badge-medium" };
        return { name: "Low Risk", color: "#10b981", class: "badge-low" };
    }

    selectCell(consequence, likelihood) {
        if (this.props.readonly) {
            return;
        }
        // Update both fields on the active Odoo 17 model record
        if ("severity_level" in this.props.record.data) {
            this.props.record.update({ severity_level: consequence.toString() });
        }
        if ("likelihood_level" in this.props.record.data) {
            this.props.record.update({ likelihood_level: likelihood.toString() });
        }
    }

    getCellClass(consequence, likelihood) {
        const score = consequence * likelihood;
        let baseClass = "matrix-cell-base";
        if (score >= 16) baseClass += " cell-critical";
        else if (score >= 10) baseClass += " cell-high";
        else if (score >= 4) baseClass += " cell-medium";
        else baseClass += " cell-low";

        if (this.currentSeverity === consequence && this.currentLikelihood === likelihood) {
            baseClass += " active-selected-cell pulse-ring";
        }
        return baseClass;
    }

    get matrixRows() {
        const rows = [];
        for (let l = 5; l >= 1; l--) {
            const cols = [];
            for (let c = 1; c <= 5; c++) {
                cols.push({
                    consequence: c,
                    likelihood: l,
                    score: c * l,
                    class: this.getCellClass(c, l),
                    isSelected: this.currentSeverity === c && this.currentLikelihood === l,
                });
            }
            rows.push({ likelihood: l, cols: cols });
        }
        return rows;
    }
}

export const hseRiskMatrixWidget = {
    component: HseRiskMatrixWidget,
    supportedTypes: ["char", "integer", "selection"],
};

registry.category("fields").add("hse_risk_matrix", hseRiskMatrixWidget);
