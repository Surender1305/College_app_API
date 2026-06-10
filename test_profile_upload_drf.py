import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from io import BytesIO

User = get_user_model()
student = User.objects.get(username="student_test")
token = str(RefreshToken.for_user(student).access_token)

client = APIClient()
client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

dummy_image = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
fp = BytesIO(dummy_image)
fp.name = "test.png"

response = client.patch(
    "/api/users/settings/",
    {"profile_picture": fp},
    format="multipart"
)

print("Status Code:", response.status_code)
print("Response Data:", response.data if hasattr(response, 'data') else response.content)
