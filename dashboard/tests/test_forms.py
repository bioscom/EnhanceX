from django.test import TestCase
from Fit4.forms import *

class TaskFormTest(TestCase):
    def test_valid_form(self):
        form = InitiativeForm(data={'initiative_name': 'Form Task', 'mark_as_confidential': False})
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        form = InitiativeForm(data={'initiative_name': ''})
        self.assertFalse(form.is_valid())