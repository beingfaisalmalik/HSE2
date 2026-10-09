/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class HseGasGaugeWidget extends Component {
    static template = "hse.GasGaugeWidget";
    static props = {
        ...standardFieldProps,
    };

    get gasTests() {
        const tests = this.props.record.data.gas_test_ids;
        if (!tests || !tests.records || tests.records.length === 0) {
            return null;
        }
        // Latest test is the first one since order is test_time desc
        const latest = tests.records[0].data;
        return {
            time: latest.test_time ? latest.test_time.toFormat("yyyy-MM-dd HH:mm") : "N/A",
            tester: latest.tester_name || "Certified AGT",
            o2: latest.oxygen_percent !== undefined ? latest.oxygen_percent : 20.9,
            lel: latest.lel_percent !== undefined ? latest.lel_percent : 0.0,
            h2s: latest.h2s_ppm !== undefined ? latest.h2s_ppm : 0.0,
            co: latest.co_ppm !== undefined ? latest.co_ppm : 0.0,
            isSafe: latest.is_safe_to_work !== undefined ? latest.is_safe_to_work : true,
        };
    }

    get o2Status() {
        const val = this.gasTests ? this.gasTests.o2 : 20.9;
        const isOk = val >= 19.5 && val <= 23.5;
        return {
            val: val,
            isOk: isOk,
            pct: Math.min(Math.max((val / 25) * 100, 0), 100),
            color: isOk ? "#10b981" : "#ef4444",
            label: isOk ? "Normal Safe (19.5 - 23.5%)" : "CRITICAL ASPHYXIATION / ENRICHMENT",
        };
    }

    get lelStatus() {
        const val = this.gasTests ? this.gasTests.lel : 0.0;
        const isOk = val < 5.0;
        return {
            val: val,
            isOk: isOk,
            pct: Math.min(Math.max((val / 20) * 100, 0), 100),
            color: isOk ? "#10b981" : "#ef4444",
            label: isOk ? "Safe (< 5% LEL)" : "EXPLOSION HAZARD DETECTED",
        };
    }

    get h2sStatus() {
        const val = this.gasTests ? this.gasTests.h2s : 0.0;
        const isOk = val < 5.0;
        return {
            val: val,
            isOk: isOk,
            pct: Math.min(Math.max((val / 15) * 100, 0), 100),
            color: isOk ? "#10b981" : "#ef4444",
            label: isOk ? "Safe (< 5 ppm)" : "TOXIC H₂S DANGER",
        };
    }

    get coStatus() {
        const val = this.gasTests ? this.gasTests.co : 0.0;
        const isOk = val < 25.0;
        return {
            val: val,
            isOk: isOk,
            pct: Math.min(Math.max((val / 50) * 100, 0), 100),
            color: isOk ? "#10b981" : "#ef4444",
            label: isOk ? "Safe (< 25 ppm)" : "TOXIC CO DANGER",
        };
    }
}

export const hseGasGaugeWidget = {
    component: HseGasGaugeWidget,
    supportedTypes: ["boolean", "char", "selection"],
};

registry.category("fields").add("hse_gas_gauge", hseGasGaugeWidget);
