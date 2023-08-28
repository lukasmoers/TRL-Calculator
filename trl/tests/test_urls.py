import os, sys, datetime
from http import HTTPStatus
from django.urls import reverse
from django.test import TestCase, Client
from django.utils.timezone import make_aware                    
from trl.models import UserProfile, Project, Level, Technology, Category

sys.stdout = open(os.devnull, 'w')

class TestUrls(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserProfile.objects.get_or_create(guid = "2546875d", full_name = "John Doe", password = "1234")
        owner = UserProfile.objects.get(guid = "2546875d")
        both_technology = Technology.objects.create(technology = "both", icon = "icons/both.png")
        trl_category = Category.objects.create(category = "trl", icon = "icons/trl.png")
        level_1 = Level.objects.create(number = 1, title = "Level 1", description = "Level 1 description")
        level_2 = Level.objects.create(number = 2, title = "Level 2", description = "Level 2 description")    
        level_9 = Level.objects.create(number = 9, title = "Level 9", description = "Level 9 description")  
        self.project_1 = Project.objects.create(name = "Project 1",
                                           technology = both_technology,
                                           level = level_1,
                                           level_semi = level_2,
                                           owner = owner)
        self.project_1.categories.add(trl_category)
        
    def test_home(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'trl/home.html')

    def test_about(self):
        url = reverse('trl:about')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'trl/about.html')
        
    def test_local_register(self):
        url = reverse('trl:register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'trl/local_register.html')
        
    def test_local_login(self):
        url = reverse('trl:login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'trl/local_login.html')

    def test_logout(self):
        self.client.login(guid='2546875d', password="1234")
        url = reverse('trl:logout')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'trl/local_login.html')
    
    def test_portfolio(self):
        self.client.login(guid='2546875d', password="1234")
        url = reverse('trl:portfolio')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'trl/portfolio.html')
    
    def test_new_project_details(self):
        self.client.login(guid='2546875d', password="1234")
        url = reverse('trl:new_project_details')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'trl/new_project_details.html')
    
    def test_update_project_details(self):
        self.client.login(guid='2546875d', password="1234")
        url = reverse('trl:update_project_details', args=[self.project_1.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'trl/update_project_details.html')
    
    def test_project_level_requirements(self):
        self.client.login(guid='2546875d', password="1234")
        url = reverse('trl:project_level_requirements', args=[self.project_1.pk, 1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'trl/project_level_requirements.html')

    def test_project_overview(self):
        self.client.login(guid='2546875d', password="1234")
        url = reverse('trl:project_overview', args=[self.project_1.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'trl/project_overview.html')