from django.test import TestCase
from .models import User

class UserTests(TestCase):
    def test_create_user(self):
        user = User.objects.create(
            name="Test User",
            nickname="testuser",
            phone="1234567890"
        )
        self.assertEqual(user.nickname, "testuser")

