import requests

# 1. Login to get token
login_url = "http://localhost:8000/api/users/login/"
# We will run the django server or query directly. Let's see if we can query django views directly by importing django.
# Let's import django and call the client.
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from users.models import Profile

User = get_user_model()
# Get or create a test student
student, _ = User.objects.get_or_create(username="student_test", email="student@pjp.edu", role="STUDENT")
student.set_password("student123")
student.save()

# Log in using django test client
client = Client()
# Get SimpleJWT token
from rest_framework_simplejwt.tokens import RefreshToken
token = str(RefreshToken.for_user(student).access_token)

# Prepare dummy image bytes
dummy_image = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"

from io import BytesIO
fp = BytesIO(dummy_image)
fp.name = "test.png"

response = client.patch(
    "/api/users/settings/",
    {"profile_picture": fp},
    format="multipart",
    HTTP_AUTHORIZATION=f"Bearer {token}"
)

print("Status Code:", response.status_code)
print("Response Data:", response.content)
