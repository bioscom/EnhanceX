from django.test import TestCase, Client
from django.urls import reverse
from Fit4.models import *
from django.shortcuts import render

class TaskListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        Initiative.objects.create(initiative_name='Sample Task')

    def test_task_list_view(self):
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sample Task')
        
def task_list(request):
    tasks = Initiative.objects.all()
    return render(request, 'tasks/task_list.html', {'tasks': tasks})