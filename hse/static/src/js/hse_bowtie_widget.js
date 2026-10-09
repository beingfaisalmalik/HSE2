/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class HseBowtieWidget extends Component {
    static template = "hse.BowtieWidget";
    static props = {
        ...standardFieldProps,
    };

    get preventiveBarriers() {
        const barriers = this.props.record.data.bowtie_barrier_ids;
        if (!barriers || !barriers.records) return [];
        return barriers.records
            .filter((r) => r.data.side === "preventive")
            .map((r) => ({
                id: r.data.id,
                name: r.data.barrier_name || "Barrier",
                type: r.data.barrier_category || "engineered_active",
                threat: r.data.threat_or_consequence || "Initiating Threat",
                status: r.data.barrier_status || "effective",
                failure: r.data.failure_mechanism || "",
            }));
    }

    get mitigativeBarriers() {
        const barriers = this.props.record.data.bowtie_barrier_ids;
        if (!barriers || !barriers.records) return [];
        return barriers.records
            .filter((r) => r.data.side === "mitigative")
            .map((r) => ({
                id: r.data.id,
                name: r.data.barrier_name || "Barrier",
                type: r.data.barrier_category || "engineered_active",
                consequence: r.data.threat_or_consequence || "Consequence",
                status: r.data.barrier_status || "effective",
                failure: r.data.failure_mechanism || "",
            }));
    }

    get topEventTitle() {
        return this.props.record.data.summary || "Loss of Primary Containment / Hazard Release";
    }

    getBarrierBadge(status) {
        if (status === "effective") return { text: "Effective", class: "bg-success" };
        if (status === "degraded") return { text: "Degraded", class: "bg-warning text-dark" };
        return { text: "Failed / Defeated", class: "bg-danger" };
    }
}

export const hseBowtieWidget = {
    component: HseBowtieWidget,
    supportedTypes: ["char", "selection", "one2many", "many2one"],
};

registry.category("fields").add("hse_bowtie", hseBowtieWidget);
