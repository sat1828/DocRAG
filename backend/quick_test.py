import sys
sys.path.insert(0, '.')

# Remove old test db
import os
if os.path.exists('test.db'):
    os.remove('test.db')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Try registration
response = client.post('/api/auth/register', 
                        json={'email': 'final_test@example.com', 
                             'password': 'TestPass123!'})

print('Status:', response.status_code)
print('Response:', response.json())

# Clean up
if os.path.exists('test.db'):
    os.remove('test.db')
