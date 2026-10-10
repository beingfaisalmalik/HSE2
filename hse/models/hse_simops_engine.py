# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import math

class HseSimopsMatrix(models.Model):
    _name = 'hse.simops.matrix'
    _description = 'Simultaneous Operations (SIMOPS) Permitted Activity Matrix'
    _order = 'activity_type_a asc'

    name = fields.Char(string='Rule Name', compute='_compute_name', store=True)
    activity_type_a = fields.Selection([
        ('hot_work', 'Hot Work (Welding, Cutting, Grinding)'),
        ('cold_work', 'Cold Work (Mechanical Maintenance)'),
        ('confined_space', 'Confined Space Entry'),
        ('critical_lift', 'Critical Crane Lift'),
        ('radiography', 'Non-Destructive Radiography (Gamma/X-Ray)'),
        ('line_break', 'Process Line Break / Hydrocarbon Opening'),
        ('high_voltage', 'High Voltage Electrical Switching'),
        ('pressure_testing', 'High-Pressure Hydrostatic / Pneumatic Testing'),
    ], string='Primary Activity A', required=True)

    activity_type_b = fields.Selection([
        ('hot_work', 'Hot Work (Welding, Cutting, Grinding)'),
        ('cold_work', 'Cold Work (Mechanical Maintenance)'),
        ('confined_space', 'Confined Space Entry'),
        ('critical_lift', 'Critical Crane Lift'),
        ('radiography', 'Non-Destructive Radiography (Gamma/X-Ray)'),
        ('line_break', 'Process Line Break / Hydrocarbon Opening'),
        ('high_voltage', 'High Voltage Electrical Switching'),
        ('pressure_testing', 'High-Pressure Hydrostatic / Pneumatic Testing'),
    ], string='Co-Located Activity B', required=True)

    compatibility = fields.Selection([
        ('prohibited', 'PROHIBITED (Hard Block - Unacceptable SIMOPS Hazard)'),
        ('restricted', 'RESTRICTED (Tier 3 Executive Authorization & Continuous Watch)'),
        ('caution', 'CAUTION (Requires Physical Separation Barrier & Gas Monitor)'),
        ('compatible', 'COMPATIBLE (Standard Precautions)'),
    ], string='SIMOPS Interlock Status', default='restricted', required=True)

    min_separation_distance_m = fields.Float(string='Minimum Separation Distance (m)', default=30.0)
    mitigation_required = fields.Text(string='Mandatory Mitigations & Controls')

    @api.depends('activity_type_a', 'activity_type_b', 'compatibility')
    def _compute_name(self):
        for rec in self:
            rec.name = "%s vs %s [%s]" % (
                rec.activity_type_a or '',
                rec.activity_type_b or '',
                (rec.compatibility or '').upper()
            )


class HseSimopsRadarPlot(models.Model):
    _name = 'hse.simops.radar.plot'
    _description = 'Plant Spatial SIMOPS Radar Coordinate Plot'
    _order = 'create_date desc'

    name = fields.Char(string='Operation Identifier', required=True)
    location_id = fields.Many2one('hse.location.profile', string='Plant Unit / Zone', required=True)
    grid_zone = fields.Char(string='Plant Grid Reference', required=True)

    # 2D Cartesian Coordinates on Plant Plan (Meters from Plant Datum 0,0)
    coord_x = fields.Float(string='Plant Coordinate X (m)', default=100.0, required=True)
    coord_y = fields.Float(string='Plant Coordinate Y (m)', default=100.0, required=True)
    hazard_radius_m = fields.Float(string='Hazard Exclusion Radius (m)', default=25.0, required=True)

    source_type = fields.Selection([
        ('hot_work', 'Hot Work Permit'),
        ('cold_work', 'Cold Work Permit'),
        ('confined_space', 'Confined Space Entry'),
        ('critical_lift', 'Crane Critical Lift Path'),
        ('radiography', 'Radiography Controlled Boundary'),
        ('line_break', 'Line Break / Flange Opening'),
        ('safety_bypass', 'Safety System Override / Bypass'),
    ], string='Operational Activity Type', required=True)

    permit_id = fields.Many2one('hse.permit', string='Related Work Permit')
    active = fields.Boolean(string='Active Operation', default=True)

    # Real-time collision detection
    has_conflict = fields.Boolean(string='SIMOPS Conflict Detected', compute='_compute_simops_collisions')
    conflict_count = fields.Integer(string='Overlapping Operations Count', compute='_compute_simops_collisions')
    conflict_summary = fields.Text(string='Conflict Conflict Details', compute='_compute_simops_collisions')

    @api.depends('location_id', 'coord_x', 'coord_y', 'hazard_radius_m', 'source_type', 'active')
    def _compute_simops_collisions(self):
        Matrix = self.env['hse.simops.matrix']
        for rec in self:
            if not rec.active:
                rec.has_conflict = False
                rec.conflict_count = 0
                rec.conflict_summary = ''
                continue

            others = self.search([
                ('id', '!=', rec.id),
                ('active', '=', True),
                # Coordinates are scoped to the modeled plant unit/zone; an
                # identical coordinate in another location is not co-located.
                ('location_id', '=', rec.location_id.id),
            ])
            conflicts = []
            for other in others:
                # Euclidean distance
                dist = math.sqrt(((rec.coord_x - other.coord_x) ** 2) + ((rec.coord_y - other.coord_y) ** 2))
                sum_radii = rec.hazard_radius_m + other.hazard_radius_m
                if dist < sum_radii:
                    # Check compatibility matrix
                    rule = Matrix.search([
                        '|',
                        '&', ('activity_type_a', '=', rec.source_type), ('activity_type_b', '=', other.source_type),
                        '&', ('activity_type_a', '=', other.source_type), ('activity_type_b', '=', rec.source_type),
                    ], limit=1)
                    compat_level = rule.compatibility if rule else 'caution'
                    conflicts.append("Conflict with [%s] (%s): Distance %.1fm < Required %.1fm [%s]" % (
                        other.name, other.source_type, dist, sum_radii, compat_level
                    ))

            rec.conflict_count = len(conflicts)
            rec.has_conflict = len(conflicts) > 0
            rec.conflict_summary = "\n".join(conflicts) if conflicts else 'No spatial overlap detected with active operations.'
