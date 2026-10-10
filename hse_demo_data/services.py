"""Read-only client-demo catalog resolution using the caller's Odoo access rights."""
from urllib.parse import urlencode

from .demo_catalog import CATEGORIES, MODULES, REPORTS, SCENARIOS


def resolve(env, xmlid):
    if '.' not in xmlid:
        xmlid = 'hse_demo_data.' + xmlid
    record = env.ref(xmlid, raise_if_not_found=False)
    if not record or not record.exists():
        return None
    record.check_access_rights('read')
    record.check_access_rule('read')
    return record


def resolve_action(env, xmlid):
    # Odoo itself resolves fixed navigation/report actions with elevated access
    # (_for_xml_id). Ordinary internal users do not have raw action-model ACLs.
    # Only curated metadata is elevated; sample records and counts never are.
    record = env.ref(xmlid, raise_if_not_found=False)
    if not record:
        return None
    if record._name not in ('ir.actions.act_window', 'ir.actions.client', 'ir.actions.report'):
        raise ValueError('Unexpected client-demo action model: ' + record._name)
    return record.sudo().exists() or None


def record_url(record):
    return '/web#' + urlencode({'id': record.id, 'model': record._name, 'view_type': 'form'})


def record_label(record):
    for field in ('title', 'product_name', 'job_task_name', 'worker_name', 'name', 'tag_number'):
        if field in record._fields and record[field]:
            return record[field]
    return record.display_name


def build_demo_context(env):
    modules, issues, counts = [], [], {}
    categories = {row['key']: row['title'] for row in CATEGORIES}
    for definition in MODULES:
        item = dict(definition)
        model = item['model']
        if model not in counts:
            counts[model] = env[model].search_count([])
        item['count'] = counts[model]
        item['category_title'] = categories[item['category']]
        action = resolve_action(env, item['action'])
        sample = resolve(env, item['sample'])
        item['ready'] = bool(action and sample and item['count'] and action.res_model == model)
        item['url'] = '/web#action=%s' % action.id if action else ''
        item['sample_url'] = record_url(sample) if sample else ''
        item['sample_label'] = record_label(sample) if sample else 'Missing sample'
        item['sample_state'] = ''
        if sample and 'state' in sample._fields:
            field = sample._fields['state']
            selection = dict(field._description_selection(env)) if field.type == 'selection' else {}
            item['sample_state'] = selection.get(sample.state, sample.state) or ''
        if not item['ready']:
            issues.append('Missing sample, action or records: ' + item['title'])
        modules.append(item)

    scenarios = []
    for definition in SCENARIOS:
        scenario = dict(definition)
        scenario['steps'] = []
        for definition_step in definition['steps']:
            item = dict(definition_step)
            sample = resolve(env, item['record'])
            item['url'] = record_url(sample) if sample else ''
            item['label'] = record_label(sample) if sample else 'Missing sample'
            item['ready'] = bool(sample)
            if not sample:
                issues.append('Missing journey record: ' + item['title'])
            scenario['steps'].append(item)
        scenarios.append(scenario)

    reports = []
    for definition in REPORTS:
        item = dict(definition)
        report, sample = resolve_action(env, item['action']), resolve(env, item['record'])
        item['ready'] = bool(report and sample and report.model == sample._name)
        if item['ready']:
            path = '%s/%s' % (report.report_name, sample.id)
            item['html_url'] = '/report/html/' + path
            item['pdf_url'] = '/report/pdf/' + path
        else:
            issues.append('Missing or mismatched report sample: ' + item['title'])
            item['html_url'] = item['pdf_url'] = ''
        reports.append(item)

    marker = env.ref('hse_demo_data.dd_enrichment_marker', raise_if_not_found=False)
    # Only this non-sensitive installation date is elevated, never the catalog
    # records/counts or any credential/configuration values supplied by a user.
    seed_date = marker.sudo().value if marker else 'Not initialized'
    ready_count = sum(item['ready'] for item in modules)
    dashboard = resolve_action(env, 'hse.action_hse_dashboard_client')
    return {
        'categories': CATEGORIES, 'modules': modules, 'scenarios': scenarios,
        'reports': reports, 'issues': issues, 'ready_count': ready_count,
        'module_count': len(modules), 'category_count': len(CATEGORIES),
        'journey_minutes': sum(scenario['minutes'] for scenario in scenarios),
        'record_count': sum(counts.values()), 'seed_date': seed_date,
        'pdf_available': env['ir.actions.report'].get_wkhtmltopdf_state() == 'ok',
        'dashboard_url': '/web#action=%s' % dashboard.id if dashboard else '/web',
        'presenter_name': env.user.name,
    }


def build_walkthrough(context):
    lines = [
        '# HSE Enterprise Suite — Client Demo Walkthrough', '',
        '## Northstar Petrochemicals (fictional demonstration facility)', '',
        'Installation date: %s. Sample dates are anchored to this date.' % context['seed_date'],
        'Coverage: %s module areas, %s categories, %s guided journeys.' % (
            context['module_count'], context['category_count'], len(context['scenarios'])), '',
        'Use an isolated database only. All people, measurements, IDs, contacts and costs are synthetic.',
        'This demo is not clinical advice, an official SDS, certified QRA, or proof of regulatory compliance.',
        'No external agency notification, physical access gate or ERP asset connector is configured.', '',
        '## Suggested agenda', '',
        '- 15 minutes: executive dashboard, incident journey highlights and contractor portal.',
        '- 45 minutes: dashboard; incident, work, process-safety and workforce journeys; reports.',
        '- 90 minutes: all eight journeys (80 minutes), plus introduction and client Q&A (10 minutes).',
        '- Use native forms for workflow exercises. Actions mutate data; rebuild for a pristine repeat.',
        '- Counts and time-sensitive statuses can change; confirm readiness before each session.', '',
        '## Live entry points', '',
        '- Client hub: /hse/demo', '- Executive dashboard: %s' % context['dashboard_url'],
        '- Frontline portal: /hse/portal (use hse.contractor in a private browser window)',
        '- Role logins: hse.presenter and hse.contractor; provision passwords outside the addon.', '',
    ]
    for scenario in context['scenarios']:
        lines += ['## %s. %s (%s minutes)' % (scenario['number'], scenario['title'], scenario['minutes']),
                  '', 'Presenter persona: ' + scenario['persona'], '', scenario['outcome'], '']
        for index, item in enumerate(scenario['steps'], 1):
            lines += ['### %s. %s' % (index, item['title']), '', item['narrative'], '',
                      '**Expected evidence:** ' + item['proof'], '',
                      '**Open record:** ' + item['url'], '']
    lines += ['## Full module coverage', '']
    for category in context['categories']:
        lines += ['### ' + category['title'], '']
        for item in context['modules']:
            if item['category'] == category['key']:
                lines += ['- **%s** — %s Sample: `%s`.' % (
                    item['title'], item['description'], item['sample'])]
        lines.append('')
    lines += ['## Reports', '']
    for report in context['reports']:
        lines.append('- %s — %s' % (report['title'], report['html_url']))
    lines += ['', 'HTML reports are always available. Native PDF export requires a working wkhtmltopdf engine.',
              'Use browser Print → Save as PDF for HTML reports if the server PDF engine is unavailable.', '',
              '## Known boundaries', '',
              '- PSSR completion is computed from checklist lines; the current commissioning action does not enforce that gate.',
              '- Exposure limits, greenhouse-gas factors and consequence formulas are illustrative and need site-specific validation.',
              '- The demo presenter is an internal HSE user. Existing internal ACLs are broad; this is not a proof of production segregation of duties.',
              '- Use synthetic medical data only. Review health-data privacy and access controls before deployment.',
              '- Re-evaluating a training matrix replaces its lines. Reset before repeating the original five-row story.',
              '- Do not send sample emails or connect this database to production mail, SMS, agency or access-control systems.', '']
    return '\n'.join(lines)
