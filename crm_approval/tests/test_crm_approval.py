# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from odoo import fields


class TestCrmApproval(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create res.users for testing
        cls.salesman = cls.env['res.users'].create({
            'name': 'Test Salesman',
            'login': 'salesman_test',
            'email': 'salesman@test.com',
            'group_ids': [(4, cls.env.ref('sales_team.group_sale_salesman_all_leads').id)],
        })

        cls.approver = cls.env['res.users'].create({
            'name': 'Test Approver',
            'login': 'approver_test',
            'email': 'approver@test.com',
            'group_ids': [(4, cls.env.ref('sales_team.group_sale_salesman_all_leads').id)],
        })

        cls.other_user = cls.env['res.users'].create({
            'name': 'Test Other User',
            'login': 'other_test',
            'email': 'other@test.com',
            'group_ids': [(4, cls.env.ref('sales_team.group_sale_salesman_all_leads').id)],
        })

        # Create custom test group
        cls.approver_group = cls.env['res.groups'].create({
            'name': 'Test Approver Group',
            'privilege_id': cls.env.ref('sales_team.res_groups_privilege_sales').id,
        })

        # Create stages
        cls.stage_normal = cls.env['crm.stage'].create({
            'name': 'Normal Stage',
            'require_approval': False,
            'sequence': 10,
        })

        cls.stage_approval_user = cls.env['crm.stage'].create({
            'name': 'User Approval Stage',
            'require_approval': True,
            'approval_type': 'user',
            'approval_user_id': cls.approver.id,
            'sequence': 20,
        })

        cls.stage_approval_group = cls.env['crm.stage'].create({
            'name': 'Group Approval Stage',
            'require_approval': True,
            'approval_type': 'group',
            'approval_group_id': cls.approver_group.id,
            'sequence': 30,
        })

    def test_crm_stage_approval_config(self):
        """Verify CRM stage validation constraints and approval helper."""
        # 1. require_approval=True with specific user but no user set -> should fail
        with self.assertRaises(ValidationError):
            self.env['crm.stage'].create({
                'name': 'Invalid Stage 1',
                'require_approval': True,
                'approval_type': 'user',
                'approval_user_id': False,
            })

        # 2. require_approval=True with group but no group set -> should fail
        with self.assertRaises(ValidationError):
            self.env['crm.stage'].create({
                'name': 'Invalid Stage 2',
                'require_approval': True,
                'approval_type': 'group',
                'approval_group_id': False,
            })

        # 3. test can_user_approve helper
        # Specific user stage: only cls.approver can approve
        self.assertTrue(self.stage_approval_user.can_user_approve(self.approver))
        self.assertFalse(self.stage_approval_user.can_user_approve(self.other_user))

        # Group stage: users in group can approve
        self.assertFalse(self.stage_approval_group.can_user_approve(self.other_user))
        self.approver_group.write({'user_ids': [(4, self.other_user.id)]})
        self.assertTrue(self.stage_approval_group.can_user_approve(self.other_user))

    def test_crm_lead_approval_flow_user(self):
        """Test the full stage approval process for specific user approval."""
        # 1. Create a lead in normal stage
        lead = self.env['crm.lead'].with_user(self.salesman).create({
            'name': 'Test Opportunity',
            'stage_id': self.stage_normal.id,
        })
        self.assertEqual(lead.approval_state, 'not_required')

        # 2. Move lead to approval stage (specific user approval)
        lead.with_user(self.salesman).write({'stage_id': self.stage_approval_user.id})
        self.assertEqual(lead.approval_state, 'pending')
        self.assertEqual(lead.previous_stage_id, self.stage_normal)

        # Verify a crm.lead.approval record is created with state 'pending'
        approvals = lead.approval_ids
        self.assertEqual(len(approvals), 1)
        self.assertEqual(approvals.stage_id, self.stage_approval_user)
        self.assertEqual(approvals.state, 'pending')

        # 3. Try to move lead to another stage without approval -> should raise UserError
        with self.assertRaises(UserError):
            lead.with_user(self.salesman).write({'stage_id': self.stage_normal.id})

        # 4. Try to approve as unauthorized user -> should raise UserError
        with self.assertRaises(UserError):
            lead.with_user(self.other_user).action_approve()

        # 5. Approve as authorised user
        lead.with_user(self.approver).action_approve()

        # The lead should automatically move to stage_approval_group and be pending
        self.assertEqual(lead.stage_id, self.stage_approval_group)
        self.assertEqual(lead.approval_state, 'pending')

        # Grant approval for the group stage (first add approver to the group)
        self.approver_group.write({'user_ids': [(4, self.approver.id)]})
        lead.with_user(self.approver).action_approve()

        # It should move to the next stage in the system (the default 'Won' stage)
        won_stage = self.env['crm.stage'].search([('is_won', '=', True)], limit=1)
        self.assertEqual(lead.stage_id, won_stage)
        self.assertEqual(lead.approval_state, 'not_required')
        self.assertFalse(lead.previous_stage_id)

        # 6. Now that it is approved, move it out to another stage (back to normal)
        lead.with_user(self.salesman).write({'stage_id': self.stage_normal.id})
        self.assertEqual(lead.approval_state, 'not_required')

    def test_crm_lead_refusal_flow(self):
        """Test rejection flow using the wizard."""
        # Create lead in normal stage
        lead = self.env['crm.lead'].with_user(self.salesman).create({
            'name': 'Test Rejection Opportunity',
            'stage_id': self.stage_normal.id,
        })

        # Move to approval stage
        lead.with_user(self.salesman).write({'stage_id': self.stage_approval_user.id})
        self.assertEqual(lead.approval_state, 'pending')

        # Get the refuse wizard action
        refuse_action = lead.with_user(self.approver).action_refuse()
        self.assertEqual(refuse_action['res_model'], 'crm.lead.refuse.wizard')

        # Create and run wizard
        wizard_ctx = refuse_action['context']
        wizard = self.env['crm.lead.refuse.wizard'].with_user(self.approver).with_context(wizard_ctx).create({
            'reason': 'Expected revenue is too low.',
        })

        # Confirm refuse
        wizard.action_confirm_refuse()

        # Verify lead is reverted to previous stage (Normal Stage)
        self.assertEqual(lead.stage_id, self.stage_normal)
        self.assertEqual(lead.approval_state, 'not_required')
        self.assertFalse(lead.previous_stage_id)

        # Verify the refusal record in history
        refusal_log = self.env['crm.lead.approval'].search([
            ('lead_id', '=', lead.id),
            ('stage_id', '=', self.stage_approval_user.id),
            ('state', '=', 'refused'),
        ])
        self.assertTrue(refusal_log)
        self.assertEqual(refusal_log.note, 'Expected revenue is too low.')
        self.assertEqual(refusal_log.approver_user_id, self.approver)
