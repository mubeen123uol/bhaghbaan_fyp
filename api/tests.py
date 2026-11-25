from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from accounts.models import User
from plants.models import Plant

class APITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='api_tester',
            password='testpassword123',
            role='HOMEOWNER',
            city='Lahore'
        )
        self.plant = Plant.objects.create(
            name_en="Mint",
            name_ur="پودینہ",
            scientific_name="Mentha spicata test",
            watering_interval_days=1,
            fertilizer_interval_days=15
        )

    def test_jwt_token_obtain(self):
        url = reverse('api:token_obtain_pair')
        resp = self.client.post(url, {'username': 'api_tester', 'password': 'testpassword123'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

    def test_plants_api_list_and_search(self):
        url = reverse('api:plant-list')
        resp = self.client.get(url, {'search': 'پودینہ'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data['count'], 1)

    def test_openapi_schema_endpoint(self):
        url = reverse('api:schema')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_authenticated_profile_endpoint(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:auth-profile')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['username'], 'api_tester')
