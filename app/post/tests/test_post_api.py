from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Post, Item, Tag

from post.serializers import PostSerializer, PostDetailSerializer


POSTS_URL = reverse('post:post-list')


def detail_url(post_id):
    """Return post detail url"""
    return reverse('post:post-detail', args=[post_id])

def sample_tag(user, name='Casual'):
    """Create and return sample tag"""
    return Tag.objects.create(user=user, name=name)

def sample_item(user, name='shirt'):
    """Create and return sample item"""
    return Item.objects.create(user=user, name=name)

def sample_post(user, **params):
    """Create and return a sample post"""
    defaults = {
        'title': 'Sample Post'
    }
    defaults.update(params)

    return Post.objects.create(user=user, **defaults)


class PublicPostApiTest(TestCase):
    """Test unauthenticated post API access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required"""
        res = self.client.get(POSTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatePostApiTest(TestCase):
    """Test authenticated post API access"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email = 'test@outfitted.com',
            first_name = 'Test',
            surname = 'von Account',
            password = 'test123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
    
    def test_retrieve_posts(self):
        """Test retrieving a list of posts"""
        sample_post(user=self.user)
        sample_post(user=self.user)

        res = self.client.get(POSTS_URL)

        posts = Post.objects.all().order_by('-id')
        serializer = PostSerializer(posts, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
    
    def test_posts_limited_to_user(self):
        """Test retrieving posts for user"""
        user2 = get_user_model().objects.create_user(
            email = 'test2@outfitted.com',
            first_name = 'Test2',
            surname = 'von Account',
            password = 'test123'
        )
        sample_post(user2)
        sample_post(self.user)

        res = self.client.get(POSTS_URL)
            
        posts = Post.objects.all().filter(user=self.user)
        serializer = PostSerializer(posts, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_post_detail(self):
        """Test viewing a post detail"""
        post = sample_post(user=self.user)
        post.tags.add(sample_tag(user=self.user))
        post.items.add(sample_item(user=self.user))

        url = detail_url(post.id)
        res = self.client.get(url)

        serializer = PostDetailSerializer(post)
        self.assertEqual(res.data, serializer.data)
    
    def test_create_basic_post(self):
        """Test creating post"""
        payload = {
            'title': 'Summer outfit',
        }
        res = self.client.post(POSTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(post, key))
    
    def test_create_post_with_tags(self):
        """Test creating a post with tags"""
        tag1 = sample_tag(user=self.user, name='Casual')
        tag2 = sample_tag(user=self.user, name='Night out')
        payload = {
            'title': 'Test outfit',
            'tags': [tag1.id, tag2.id],
        }
        res = self.client.post(POSTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(id=res.data['id'])
        tags = post.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)
    
    def test_create_post_with_items(self):
        """Test creating post with items"""
        item1 = sample_item(user=self.user, name='Shirt')
        item2 = sample_item(user=self.user, name='Trouser')
        payload = {
            'title': 'Summer outfit',
            'items': [item1.id, item2.id],
        }
        res = self.client.post(POSTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(id=res.data['id'])
        items = post.items.all()
        self.assertEqual(items.count(), 2)
        self.assertIn(item1, items)
        self.assertIn(item1, items)