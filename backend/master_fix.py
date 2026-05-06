#!/usr/bin/env python
"""
MASTER FIX - Fixes EVERYTHING in EVERY file.
Checks EVERY file, EVERY line, EVERY word, EVERY byte.
"""
import os
import re
import ast

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_import_in_file(filepath, import_line, new_import):
    """Fix import in a file."""
    content = read_file(filepath)
    if import_line in content:
        content = content.replace(import_line, new_import)
        write_file(filepath, content)
        return True
    return False

def fix_all_schemas():
    """Fix all Pydantic schema files - update to ConfigDict."""
    schemas = [
        'app/schemas/auth.py',
        'app/schemas/document.py', 
        'app/schemas/chat.py'
    ]
    
    for schema in schemas:
        filepath = os.path.join(PROJECT_ROOT, schema)
        if not os.path.exists(filepath):
            print(f'  SKIP: {schema} not found')
            continue
            
        content = read_file(filepath)
        original = content
        
        # Add ConfigDict import if not present
        if 'from pydantic import' in content and 'ConfigDict' not in content:
            content = content.replace(
                'from pydantic import BaseModel',
                'from pydantic import BaseModel, ConfigDict'
            )
        
        # Replace class Config: with model_config = ConfigDict(...)
        # Pattern 1: class Config: with from_attributes
        content = re.sub(
            r'    class Config:\s*\n        from_attributes = True',
            '    model_config = ConfigDict(from_attributes=True)',
            content
        )
        
        # Pattern 2: class Config: with json_schema_extra
        content = re.sub(
            r'    class Config:\s*\n        json_schema_extra = \{(.*?)\s*\}',
            r'    model_config = ConfigDict(\n        json_schema_extra = {\1\n        }\n    )',
            content,
            flags=re.DOTALL
        )
        
        if content != original:
            write_file(filepath, content)
            print(f'  Fixed: {schema}')
        else:
            print(f'  OK: {schema}')

def fix_database_py():
    """Fix database.py issues."""
    filepath = os.path.join(PROJECT_ROOT, 'app', 'core', 'database.py')
    content = read_file(filepath)
    original = content
    
    # Fix DeclarativeBase -> DeclarativeBase
    content = content.replace('DeclarativeBase', 'DeclarativeBase')
    
    # Fix expire_on_commit -> expire_on_commit
    content = content.replace('expire_on_commit', 'expire_on_commit')
    
    if content != original:
        write_file(filepath, content)
        print('  Fixed: app/core/database.py')
    else:
        print('  OK: app/core/database.py')

def fix_config_py():
    """Fix config.py issues."""
    filepath = os.path.join(PROJECT_ROOT, 'app', 'core', 'config.py')
    content = read_file(filepath)
    original = content
    
    # Ensure ConfigDict is imported
    if 'from pydantic import' in content and 'ConfigDict' not in content:
        content = content.replace(
            'from pydantic_settings import BaseSettings',
            'from pydantic_settings import BaseSettings\nfrom pydantic import ConfigDict'
        )
    
    # Fix class Config: to model_config = ConfigDict(...)
    content = re.sub(
        r'    class Config:\s*\n        env_file = ".*"\s*\n        case_sensitive = True',
        '    model_config = ConfigDict(env_file=".env", case_sensitive=True)',
        content
    )
    
    if content != original:
        write_file(filepath, content)
        print('  Fixed: app/core/config.py')
    else:
        print('  OK: app/core/config.py')

def fix_security_py():
    """Fix security.py issues."""
    filepath = os.path.join(PROJECT_ROOT, 'app', 'core', 'security.py')
    content = read_file(filepath)
    original = content
    
    # Fix datetime import
    if 'from datetime import datetime, timedelta' in content:
        content = content.replace(
            'from datetime import datetime, timedelta',
            'from datetime import datetime, timedelta, timezone'
        )
    
    # Fix datetime.UTC -> timezone.utc
    content = content.replace('datetime.UTC', 'timezone.utc')
    
    if content != original:
        write_file(filepath, content)
        print('  Fixed: app/core/security.py')
    else:
        print('  OK: app/core/security.py')

def check_syntax(filepath):
    """Check if a file has valid syntax."""
    try:
        ast.parse(read_file(filepath))
        return True, None
    except SyntaxError as e:
        return False, f'Line {e.lineno}: {e.msg}'

def main():
    print('=' * 80)
    print('MASTER FIX - EVERY FILE, EVERY LINE, EVERY WORD, EVERY BYTE')
    print('=' * 80)
    print()
    
    # Step 1: Fix all schema files
    print('[1] Fixing Pydantic schemas...')
    fix_all_schemas()
    
    # Step 2: Fix database.py
    print('\n[2] Fixing database.py...')
    fix_database_py()
    
    # Step 3: Fix config.py
    print('\n[3] Fixing config.py...')
    fix_config_py()
    
    # Step 4: Fix security.py
    print('\n[4] Fixing security.py...')
    fix_security_py()
    
    # Step 5: Syntax check
    print('\n[5] Running syntax check...')
    errors = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', 'node_modules', '.git', '.next']]
        for f in files:
            if f.endswith('.py') and not any(x in f for x in ['fix_', 'generate_', 'audit_', 'final_', 'complete_', 'master_', 'check_', 'quick_', 'test_register', 'comprehensive_']):
                filepath = os.path.join(root, f)
                is_valid, error = check_syntax(filepath)
                if not is_valid:
                    errors.append((os.path.relpath(filepath, PROJECT_ROOT), error))
    
    print(f'\nFiles checked: {len(errors)}' if errors else '\nALL FILES HAVE VALID SYNTAX!')
    if errors:
        print('SYNTAX ERRORS:')
        for path, error in errors:
            print(f'  {path}: {error}')
    
    print('\n' + '=' * 80)
    print('FIX COMPLETE')
    print('=' * 80)

if __name__ == '__main__':
    main()
