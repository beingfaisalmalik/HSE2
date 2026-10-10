from odoo import api, models, _
from odoo.exceptions import AccessError

from ..seed import DemoSeeder


class HSEDemoLoader(models.AbstractModel):
    _name = 'hse.demo.loader'
    _description = 'HSE Client Demo Data Installer'

    @api.model
    def load_comprehensive_demo(self):
        if not self.env.is_admin():
            raise AccessError(_('Only an administrator can install client demo samples.'))
        DemoSeeder(self.env).run()
        return True
