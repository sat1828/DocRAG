"""Debug route registration."""
import sys
sys.path.insert(0, '.')

from app.main import app

print("=== ALL REGISTERED ROUTES ===")
for route in app.routes:
    if hasattr(route, 'path'):
        methods = getattr(route, 'methods', set())
        print(f"{', '.join(methods) if methods else 'MOUNT'}: {route.path}")

print("\n=== ROUTER DETAILS ===")
from app.routers import auth, upload, chat, admin
print(f"auth.router.routes: {len(auth.router.routes)} routes")
print(f"upload.router.routes: {len(upload.router.routes)} routes")
print(f"chat.router.routes: {len(chat.router.routes)} routes")
print(f"admin.router.routes: {len(admin.router.routes)} routes")
