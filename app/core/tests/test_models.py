from django.test import TestCase
from django.contrib.auth import get_user_model

class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """Test creating new user with email is successful"""
        email = 'test@outfitted.com'
        first_name = 'Test'
        surname = 'von Account'
        password = 'Testpass123'
        user = get_user_model().objects.create_user(
            email = email,
            first_name = first_name,
            surname = surname,
            password = password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
    
    def test_new_user_normalized(self):
        """Test the email for a new user is normalized"""
        email = 'test@OUTFITTED.com'
        user = get_user_model().objects.create_user(            
            email = email,
            first_name = 'Test',
            surname = 'von Account',
            password = 'test1234',
        )

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(   
            email = None,
            first_name = 'Test',
            surname = 'von Account',
            password = 'test1234',
        )

    def test_create_new_superuser(self):
        """Test creating a new superuser"""
        email = 'test@outfitted.com'
        first_name = 'Test'
        surname = 'von Account'
        password = 'Testpass123'
        user = get_user_model().objects.create_superuser(
            email = email,
            first_name = first_name,
            surname = surname,
            password = password
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
