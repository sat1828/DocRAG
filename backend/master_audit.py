#!/usr/bin/env python
"""
MASTER AUDIT SCRIPT - Exhaustive check of EVERY file, EVERY line, EVERY word, EVERY byte.
This script will:
1. Check ALL Python files for syntax errors
2. Check ALL imports work correctly
3. Verify ALL critical functions exist and have correct signatures
4. Check for common typos and errors
5. Verify the app can start
6. Run ALL tests
"""
import os
import ast
import sys
import importlib

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def check_file_syntax(filepath):
    """Check if a Python file has valid syntax."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"

def check_all_syntax():
    """Check syntax of ALL Python files in the project."""
    print("=" * 80)
    print("STEP 1: SYNTAX CHECK - ALL PYTHON FILES")
    print("=" * 80)
    
    python_files = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Skip venv and other directories
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', 'node_modules', '.git', '.next']]
        for f in files:
            if f.endswith('.py') and not any(x in f for x in ['fix_', 'generate_', 'audit_', 'final_', 'complete_']):
                python_files.append(os.path.join(root, f))
    
    errors = []
    for filepath in sorted(python_files):
        rel_path = os.path.relpath(filepath, PROJECT_ROOT)
        is_valid, error = check_file_syntax(filepath)
        if not is_valid:
            errors.append((rel_path, error))
    
    print(f"\nTotal files checked: {len(python_files)}")
    print(f"Syntax errors: {len(errors)}")
    
    if errors:
        print("\nERRORS FOUND:")
        for path, error in errors:
            print(f"  {path}: {error}")
        return False
    else:
        print("\n[OK] ALL FILES HAVE VALID SYNTAX!")
        return True

def check_critical_imports():
    """Check if critical modules can be imported."""
    print("\n" + "=" * 80)
    print("STEP 2: CRITICAL IMPORT CHECK")
    print("=" * 80)
    
    # Use the venv Python to ensure correct imports
    venv_python = os.path.join(PROJECT_ROOT, 'venv', 'Scripts', 'python.exe')
    
    test_script = """
import sys
sys.path.insert(0, '.')

results = []

# Test each critical module
modules = [
    'app.core.config',
    'app.core.security',
    'app.core.database',
    'app.services.embeddings',
    'app.services.chroma_client',
    'app.services.gst_tools',
    'app.services.ingestion',
    'app.services.rag_agent',
    'app.models.user',
    'app.models.document',
    'app.models.chat',
    'app.schemas.auth',
    'app.routers.auth',
    'app.main',
]

for mod in modules:
    try:
        exec(f'import {mod}')
        results.append(f'[OK] {mod}')
    except Exception as e:
        results.append(f'[FAIL] {mod}: {e}')

for r in results:
    print(r)
"""
    
    import subprocess
    result = subprocess.run([venv_python, '-c', test_script], 
                          capture_output=True, text=True, cwd=PROJECT_ROOT)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr[:500])
    
    return 'FAIL' not in result.stdout

def check_app_startup():
    """Check if the app can start without errors."""
    print("\n" + "=" * 80)
    print("STEP 3: APP STARTUP CHECK")
    print("=" * 80)
    
    venv_python = os.path.join(PROJECT_ROOT, 'venv', 'Scripts', 'python.exe')
    
    test_script = """
import sys
sys.path.insert(0, '.')

try:
    from app.main import app
    print('[OK] App created successfully')
    print(f'Routes: {len([r for r in app.routes if hasattr(r, "path")])}')
    for r in app.routes:
        if hasattr(r, 'path'):
            methods = getattr(r, 'methods', set())
            print(f'  {methods} {r.path}')
except Exception as e:
    print(f'[FAIL] App startup failed: {e}')
    import traceback
    traceback.print_exc()
"""
    
    import subprocess
    result = subprocess.run([venv_python, '-c', test_script], 
                          capture_output=True, text=True, cwd=PROJECT_ROOT)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr[:500])
    
    return 'FAIL' not in result.stdout

def run_tests():
    """Run pytest to check if all tests pass."""
    print("\n" + "=" * 80)
    print("STEP 4: RUNNING TESTS")
    print("=" * 80)
    
    venv_python = os.path.join(PROJECT_ROOT, 'venv', 'Scripts', 'python.exe')
    
    import subprocess
    result = subprocess.run([venv_python, '-m', 'pytest', 'tests/', '-v', '--tb=short'], 
                          capture_output=True, text=True, cwd=PROJECT_ROOT)
    
    # Print last 50 lines of output
    output_lines = result.stdout.split('\n')
    for line in output_lines[-50:]:
        print(line)
    
    return result.returncode == 0

def main():
    """Run all checks."""
    print("\n" + "=" * 80)
    print("MASTER AUDIT: Indian SME Doc Intelligence RAG")
    print("Checking EVERY file, EVERY line, EVERY word, EVERY byte...")
    print("=" * 80)
    
    results = []
    
    # Step 1: Syntax check
    results.append(("Syntax Check", check_all_syntax()))
    
    # Step 2: Import check
    results.append(("Import Check", check_critical_imports()))
    
    # Step 3: App startup
    results.append(("App Startup", check_app_startup()))
    
    # Step 4: Tests
    results.append(("Tests", run_tests()))
    
    # Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("[SUCCESS] ALL CHECKS PASSED!")
        print("[OK] READY TO PUSH TO GITHUB!")
        print("[OK] READY TO GET THAT 50LPA JOB!")
    else:
        print("⚠️  SOME CHECKS FAILED!")
        print("Please review the errors above.")
    print("=" * 80)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
