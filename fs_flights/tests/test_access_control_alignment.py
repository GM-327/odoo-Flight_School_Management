from odoo.tests.common import TransactionCase


class TestFlightAccessControlAlignment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user_group = cls.env.ref('fs_core.group_flight_school_user')
        manager_group = cls.env.ref('fs_core.group_flight_school_manager')
        cls.basic_user = cls.env['res.users'].create({
            'name': 'Flight Read-Only User',
            'login': 'flight.readonly@example.com',
            'group_ids': [(6, 0, [user_group.id])],
        })
        cls.manager_user = cls.env['res.users'].create({
            'name': 'Flight Operations Manager',
            'login': 'flight.manager@example.com',
            'group_ids': [(6, 0, [manager_group.id])],
        })

    def test_base_users_cannot_mutate_operations_or_flights(self):
        for model_name in (
            'fs.flight',
            'fs.daily.operations',
            'fs.simulator.operations',
        ):
            model = self.env[model_name].with_user(self.basic_user)
            self.assertFalse(model.has_access('create'))
            self.assertFalse(model.has_access('write'))
            self.assertTrue(self.env[model_name].with_user(self.manager_user).has_access('create'))
            self.assertTrue(self.env[model_name].with_user(self.manager_user).has_access('write'))

    def test_only_managers_can_open_operation_wizards(self):
        for model_name in (
            'fs.flight.cancel.wizard',
            'fs.add.flight.wizard',
            'fs.add.sim.wizard',
            'fs.flight.delete.wizard',
            'fs.import.schedule.wizard',
        ):
            self.assertFalse(self.env[model_name].with_user(self.basic_user).has_access('create'))
            self.assertTrue(self.env[model_name].with_user(self.manager_user).has_access('create'))
