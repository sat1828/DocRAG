import sys
sys.path.insert(0, '.')

# Ensure clean state
import os
if os.path.exists('test.db'):
    os.remove('test.db')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Test registration
response = client.post('/api/auth/register', 
                      json={'email': 'check_error@example.com', 
                           'password': 'TestPass123!'})

print('Status:', response.status_code)
print('Response:', response.json())

# Cleanup
if os.path.exists('test.db'):
    os.remove('test.db')
