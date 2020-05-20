import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Post, Item, Tag

from post.serializers import PostSerializer, PostDetailSerializer


POSTS_URL = reverse('post:post-list')


def image_upload_url(post_id):
    """Return URL for post image upload"""
    return reverse('post:post-upload-image', args=[post_id])


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

    def test_partial_update_post(self):
        """Test updating a post with patch"""
        post = sample_post(user=self.user)
        post.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='Belt')

        payload = {
            'title': 'Autumn Outfit',
            'tags': [new_tag.id]
        }
        url = detail_url(post.id)
        self.client.patch(url, payload)

        post.refresh_from_db()
        self.assertEqual(post.title, payload['title'])
        tags = post.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_post(self):
        """Test updating a post with a put"""
        post = sample_post(user=self.user)
        post.tags.add(sample_tag(user=self.user))

        payload = {
            'title': 'Spring Outfit',
        }
        url = detail_url(post.id)
        self.client.put(url, payload)

        post.refresh_from_db()
        self.assertEqual(post.title, payload['title'])
        tags = post.tags.all()
        self.assertEqual(len(tags), 0)
    
    

class PostImageUploadTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email = 'test@outfitted.com',
            first_name = 'Test',
            surname = 'von Account',
            password = 'test123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.post = sample_post(user=self.user)
    
    def tearDown(self):
        self.post.image.delete()
    
    def test_upload_image_to_post(self):
        """Test uploading an email to post"""
        url = image_upload_url(self.post.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')

        self.post.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.post.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.post.id)
        res = self.client.post(url, {'image': 'notimage'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_filter_posts_by_tags(self):
        """Test returning posts with specific tags"""
        post1 = sample_post(user=self.user, title='Thai vegetable curry')
        post2 = sample_post(user=self.user, title='Aubergine with tahini')
        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Vegetarian')
        post1.tags.add(tag1)
        post2.tags.add(tag2)
        post3 = sample_post(user=self.user, title='Fish and chips')

        res = self.client.get(
            POSTS_URL,
            {'tags': f'{tag1.id},{tag2.id}'}
        )

        serializer1 = PostSerializer(post1)
        serializer2 = PostSerializer(post2)
        serializer3 = PostSerializer(post3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)