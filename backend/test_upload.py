import requests
import os

BASE_URL = "http://localhost:8000"

# Step 1: Login to get token
print("=== Step 1: Login ===")
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"email": "notmot178@gmail.com", "password": "Test123456!"}
)
print(f"Login Status: {login_response.status_code}")

if login_response.status_code != 200:
    print("❌ Login failed")
    exit(1)

token = login_response.json()["access_token"]
print(f"✅ Token obtained: {token[:50]}...\n")

# Step 2: Create a dummy PDF file for testing
print("=== Step 2: Create test PDF ===")
test_pdf_path = "test_document.pdf"

# Create a minimal valid PDF
minimal_pdf = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<< /Size 4 /Root 1 0 R >>
startxref
190
%%EOF"""

with open(test_pdf_path, "wb") as f:
    f.write(minimal_pdf)

print(f"✅ Test PDF created: {test_pdf_path}\n")

# Step 3: Upload the PDF
print("=== Step 3: Upload PDF ===")
headers = {"Authorization": f"Bearer {token}"}

with open(test_pdf_path, "rb") as f:
    files = {"file": ("test_document.pdf", f, "application/pdf")}
    upload_response = requests.post(
        f"{BASE_URL}/api/documents/upload",
        headers=headers,
        files=files
    )

print(f"Upload Status: {upload_response.status_code}")
print(f"Response: {upload_response.json()}")

if upload_response.status_code == 201:
    print("\n✅ Upload successful!")
    doc_id = upload_response.json()["id"]
    print(f"Document ID: {doc_id}")
else:
    print(f"\n❌ Upload failed: {upload_response.json()}")

# Cleanup
if os.path.exists(test_pdf_path):
    os.remove(test_pdf_path)
    print(f"\n🗑️  Cleaned up test file")
