import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
response = client.post('/api/auth/register', json={'email': 'test4@example.com', 'password': 'TestPass123!'})

print('STATUS:', response.status_code)
print('BODY:', response.json())
