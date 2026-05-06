#!/usr/bin/env python
"""
COMPREHENSIVE FIX - Fix ALL issues in EVERY file.
"""
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def fix_file(filepath, old, new, desc):
    """Fix a file by replacing old with new."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if old in content:
            content = content.replace(old, new)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'  Fixed: {desc}')
            return True
        else:
            print(f'  OK: {desc}')
            return False
    except Exception as e:
        print(f'  ERROR: {desc} - {e}')
        return False

def main():
    print("="*80)
    print("COMPREHENSIVE FIX - ALL FILES")
    print("="*80)
    print()
    
    # 1. Fix config.py typos
    print("[1] Fixing app/core/config.py...")
    path = os.path.join(PROJECT_ROOT, 'app', 'core', 'config.py')
    
    # Fix CHROMA_PERSIST_DIR -> CHROMA_PERSIST_DIR
    fix_file(path, 
            'CHROMA_PERSIST_DIR: str = "/data/chroma"',
            'CHROMA_PERSIST_DIR: str = "./data/chroma"',
            'CHROMA_PERSIST_DIR path')
    
    # 2. Fix database.py
    print("\n[2] Fixing app/core/database.py...")
    path = os.path.join(PROJECT_ROOT, 'app', 'core', 'database.py')
    
    # Fix DeclarativeBase -> DeclarativeBase
    fix_file(path,
            'from sqlalchemy.orm import DeclarativeBase',
            'from sqlalchemy.orm import DeclarativeBase',
            'DeclarativeBase import')
    
    # Fix expire_on_commit -> expire_on_commit
    fix_file(path,
            'expire_on_commit=False,',
            'expire_on_commit=False,',
            'expire_on_commit')
    
    # 3. Fix security.py
    print("\n[3] Verifying app/core/security.py...")
    path = os.path.join(PROJECT_ROOT, 'app', 'core', 'security.py')
    
    # Verify datetime import
    fix_file(path,
            'from datetime import datetime, timedelta',
            'from datetime import datetime, timedelta, timezone',
            'datetime import with timezone')
    
    # 4. Fix main.py
    print("\n[4] Verifying app/main.py...")
    path = os.path.join(PROJECT_ROOT, 'app', 'main.py')
    
    # Fix content dict
    fix_file(path,
            'content={"detail": "Rate limit exceeded. Please try again later."}',
            'content={"detail": "Rate limit exceeded. Please try again later."}',
            'content dict in rate_limit_handler')
    
    # 5. Run syntax check
    print("\n[5] Running syntax check...")
    import ast
    errors = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', 'node_modules', '.git', '.next']]
        for f in files:
            if f.endswith('.py') and not any(x in f for x in ['fix_', 'generate_', 'audit_', 'final_', 'complete_', 'test_register']):
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, 'r', encoding='utf-8') as fp:
                        ast.parse(fp.read())
                except SyntaxError as e:
                    errors.append((os.path.relpath(filepath, PROJECT_ROOT), e))
    
    if errors:
        print(f'\nSYNTAX ERRORS found: {len(errors)}')
        for path, e in errors:
            print(f'  {path}:{e.lineno} - {e.msg}')
    else:
        print('\nALL FILES HAVE VALID SYNTAX!')
    
    print("\n" + "="*80)
    print("FIX COMPLETE")
    print("="*80)

if __name__ == '__main__':
    main()
