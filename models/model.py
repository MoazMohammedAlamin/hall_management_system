from odoo import fields, models, api


class lounge(models.Model):
    _name = "lounge.user"
    _rec_name = 'code'
    code = fields.Char(default=lambda self: ('Serial_Number'), readonly=True)
    user_id = fields.Many2one("res.users", string="Name", required=True, default=lambda self:self.env.user)
    company_id = fields.Many2one("res.company", string="Company Name", required=True, default=lambda self:self.env.user.company_id)
    date = fields.Date(string="Date", required=True, default=fields.Date.today())
    period = fields.Date(string="Wadding Time", required=True)
    meal = fields.Selection(selection=[("lunch","Lunch"),("dinner","Dinner")], default="lunch", string="Meal", required=True)
    currency_id = fields.Many2one("res.currency", required=True, default=lambda self:self.env.user.company_id.currency_id)
    person_ids = fields.One2many("lounge.person", "lounge_ids", string="line_person")
    total = fields.Float(string="Total", compute="_compute_total", store=True)
    line_water = fields.Float(string="Water", compute="_compute_total", store=True)
    line_plat = fields.Float(string="Plats", compute="_compute_total", store=True)
    line_seats = fields.Float(string="Seats", compute="_compute_total", store=True)
    line_price = fields.Float(string="Price", compute="_compute_total", store=True)

    @api.model
    def create(self,vals):
        if vals.get('code', ('Serial_Number')) == ('Serial_Number'):
            vals['code'] = self.env['ir.sequence'].next_by_code('lounge.user') or ('Serial_Number')
            dlat = super(lounge, self).create(vals)
            return dlat


    def action_view_invoice(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_in_invoice_type')
        result = action.read()[0]
        default_account = self.env['account.journal'].search([('type', '=', 'purchase')],
                                                             limit=1).default_debit_account_id or False

        person_ids = []
        for line in self.person_ids:
            person_ids.append((0, 0, {
                'price_unit' : line.total,
                'quantity': 1,
                'name' : line.name,
                'account_id': default_account.id if default_account else False,
            }))

            # if line.water:
            #     person_ids.append((0, 0, {
            #         'price_unit': float(line.water) or 1,
            #         'quantity': 1,
            #         'name': "water",
            #         'account_id': default_account.id if default_account else False,
            #     }))
            # if line.plat:
            #     person_ids.append((0, 0, {
            #         'price_unit': float(line.plat) or 1,
            #         'quantity': 1,
            #         'name': "plat",
            #         'account_id': default_account.id if default_account else False,
            #     }))
            # if line.seats:
            #     person_ids.append((0, 0, {
            #         'price_unit': float(line.seats) or 1,
            #         'quantity': 1,
            #         'name': "seats",
            #         'account_id': default_account.id if default_account else False,
            #     }))
            # if line.price:
            #     person_ids.append((0, 0, {
            #         'price_unit': float(line.price) or 1,
            #         'quantity': 1,
            #         'name': "price",
            #         'account_id': default_account.id if default_account else False,
            #     }))
            print(person_ids)
            result['context'] = {
                'default_type': 'in_invoice',
                # 'default_company_id': self.company_id.id,
                # 'default_currency_id': self.currency_id.id,
                 'default_user_id': self.user_id.id,
                'default_line_ids': person_ids,
            }
            view_id = self.env.ref('account.view_move_form', False)
            form_view = [(view_id and view_id.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            result['name'] = self.code
            result['context']['default_invoice_origin'] = self.code
            result['context']['default_ref'] = self.code
            return result





    @api.depends('person_ids')
    def _compute_total(self):
        for person in self:
            line_water = line_plat = line_seats = line_price = 0.0
            for line in person.person_ids:
                line_water += line.water
                line_plat += line.plat
                line_seats += line.seats
                line_price += line.price
                person.update({
                    'line_water':line_water,
                    'line_plat':line_plat,
                    'line_seats':line_seats,
                    'line_price':line_price,
                    'total':line_water * line_plat * line_seats * line_price,
                })

class person(models.Model):
    _name = "lounge.person"
    name = fields.Char(string="Person Name")
    water = fields.Float(string="Water")
    plat = fields.Float(string="Plats")
    seats = fields.Float(string="Seats")
    price = fields.Float(string="Price")
    total = fields.Float(string="Total", compute="_compute_total")
    lounge_ids = fields.Many2one("lounge.user", string="lounge_id")

    @api.depends('water','plat','seats','price')
    def _compute_total(self):
        for line in self:
            line.total = (line.water * line.plat * line.seats * line.price)