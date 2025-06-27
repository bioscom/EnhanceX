from django.test import SimpleTestCase
from django.urls import reverse, resolve
from dashboard.views import task_list

class TestUrls(SimpleTestCase):
    def test_task_list_url_is_resolved(self):
        url = reverse('task_list')
        self.assertEqual(resolve(url).func, task_list)