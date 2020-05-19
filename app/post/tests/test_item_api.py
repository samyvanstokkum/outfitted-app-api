from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Item

from post.serializers import ItemSerializer


ITEMS_URL = reverse('post:item-list')


class PublicItemsApiTest(TestCase):
    """Test the publicly available items API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required to access the endpoint"""
        res = self.client.get(ITEMS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    
class PrivateItemsApiTest(TestCase):
    """Test the private items api"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email = 'test@outfitted.com',
            first_name = 'Test',
            surname = 'von Account',
            password = 'test123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
    
    def test_retrieve_items_list(self):
        """Test retrieving a list of items"""
        Item.objects.create(user=self.user, name='Shirt')
        Item.objects.create(user=self.user, name='Sock')

        res = self.client.get(ITEMS_URL)

        items = Item.objects.all().order_by('-name')
        serializer = ItemSerializer(items, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_items_limited_to_user(self):
        """Test that only items for the authenticated user are returned"""
        user2 = get_user_model().objects.create_user(
            email = 'test2@outfitted.com',
            first_name = 'Test2',
            surname = 'von Account',
            password = 'test123'
        )
        Item.objects.create(user=user2, name='Pants')
        item = Item.objects.create(user=self.user, name='Hat')

        res = self.client.get(ITEMS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], item.name)
    
    def test_create_item_successful(self):
        """Test create a new item"""
        payload = {'name': 'Belt'}
        self.client.post(ITEMS_URL, payload)

        exists = Item.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()
        self.assertTrue(exists)
    
    def test_create_item_invalid(self):
        """Test creating invalid item fails"""
        payload = {'name': ''}
        res = self.client.post(ITEMS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


