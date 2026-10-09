/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class HseDispersionPlumeWidget extends Component {
    static template = "hse.DispersionPlumeWidget";
    static props = {
        ...standardFieldProps,
    };

    get scenario() {
        const d = this.props.record.data;
        return {
            name: d.name || "Chemical Release Scenario",
            chemical: d.chemical_name || "Hazardous Gas",
            windSpeed: d.wind_speed_m_s || 3.0,
            windDir: d.wind_direction_deg !== undefined ? d.wind_direction_deg : 180,
            stability: (d.stability_class || "d").toUpperCase(),
            erpg3: d.erpg_3_dist_m || 85.0,
            erpg2: d.erpg_2_dist_m || 210.0,
            erpg1: d.erpg_1_dist_m || 450.0,
            evacRadius: d.recommended_evacuation_radius_m || 500.0,
            radFire: d.rad_37_5_kw_m || 45.0,
            blastPsi: d.blast_10_psi_m || 60.0,
        };
    }

    get scale() {
        // Map maximum evacuation radius to 180px SVG radius
        const maxDist = Math.max(this.scenario.evacRadius, 100);
        return 160.0 / maxDist;
    }

    get r3() { return Math.max(this.scenario.erpg3 * this.scale, 15); }
    get r2() { return Math.max(this.scenario.erpg2 * this.scale, 35); }
    get r1() { return Math.max(this.scenario.erpg1 * this.scale, 65); }
    get rEvac() { return Math.max(this.scenario.evacRadius * this.scale, 95); }
}

export const hseDispersionPlumeWidget = {
    component: HseDispersionPlumeWidget,
    supportedTypes: ["float", "char", "integer"],
};

registry.category("fields").add("hse_dispersion_plume", hseDispersionPlumeWidget);
