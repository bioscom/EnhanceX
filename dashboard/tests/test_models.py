from django.test import TestCase
from Fit4.models import *

class TaskModelTest(TestCase):
    def test_create_task(self):
        task = Initiative.objects.create(initiative_name='Test Task')
        self.assertEqual(task.initiative_name, 'Test Task')
        self.assertFalse(task.overall_status)