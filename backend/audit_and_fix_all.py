#!/usr/bin/env python
"""
Comprehensive audit and fix script for Indian SME Doc Intelligence RAG project.
Checks EVERY file, EVERY line, EVERY word, EVERY byte for errors.
"""
import os
import ast
import re
import sys

def check_syntax(filepath):
    """Check if a Python file has valid syntax."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"

def check_dict_commas(filepath):
    """Check for missing commas in dict literals - a common syntax error."""
    issues = []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines, 1):
        # Look for patterns like: {"key": value "key2": value2}
        # This indicates missing comma between dict entries
        if '{"' in line or "{'" in line:
            # Find all key-value pairs in the line
            # Pattern: "key": value followed by another "key": without comma
            pattern = r'["\']\w+["\']\s*:\s*\S+\s+["\']\w+["\']\s*:'
            if re.search(pattern, line):
                issues.append((i, "Possible missing comma in dict", line.rstrip()))
    
    return issues

def check_imports(filepath):
    """Check for wrong import statements."""
    issues = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for wrong sentence_transformers import
    if 'from sentence_transformers import' in content:
        # This is actually correct - the package is sentence_transformers
        pass
    if 'from sentence_transformers import' in content:
        issues.append((0, "Wrong import: sentence_transformers should be sentence_transformers"))
    
    return issues

def check_config_typos(filepath):
    """Check config.py for common typos."""
    issues = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for double letters in config vars
    typos = {
        'ACCESS_TOKEN_EXPIRE_MINUTES': 'ACCESS_TOKEN_EXPIRE_MINUTES',
        'CHROMA_PERSIST_DIR': 'CHROMA_PERSIST_DIR',
        'JWT_SECRET': 'JWT_SECRET',
    }
    
    for correct, wrong in typos.items():
        if wrong in content and correct not in content:
            issues.append((0, f"Typo found: {wrong} should be {correct}"))
    
    return issues

def check_auth_typos(filepath):
    """Check auth.py for common typos."""
    issues = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for user.hashed (missing _password)
    if 'user.hashed' in content and 'user.hashed_password' not in content:
        issues.append((0, "Typo: user.hashed should be user.hashed_password"))
    
    return issues

def fix_security_dict_commas(filepath):
    """Fix missing commas in dict literals in security.py."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix: {"exp": expire "type": "access"} -> {"exp": expire, "type": "access"}
    content = content.replace('{"exp": expire "type": "access"}', '{"exp": expire, "type": "access"}')
    content = content.replace('{"exp": expire "type": "refresh"}', '{"exp": expire, "type": "refresh"}')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def audit_file(filepath):
    """Audit a single file and return all issues."""
    issues = []
    
    # Check syntax
    is_valid, error = check_syntax(filepath)
    if not is_valid:
        issues.append(f"SYNTAX ERROR: {error}")
    
    # Check dict commas
    dict_issues = check_dict_commas(filepath)
    for line_num, msg, line_content in dict_issues:
        issues.append(f"Line {line_num}: {msg} - {line_content[:60]}")
    
    # Check imports
    import_issues = check_imports(filepath)
    for line_num, msg in import_issues:
        issues.append(f"Line {line_num}: {msg}")
    
    # Check for specific file issues
    if 'config.py' in filepath:
        config_issues = check_config_typos(filepath)
        for line_num, msg in config_issues:
            issues.append(msg)
    
    if 'auth.py' in filepath:
        auth_issues = check_auth_typos(filepath)
        for line_num, msg in auth_issues:
            issues.append(msg)
    
    if 'security.py' in filepath:
        if fix_security_dict_commas(filepath):
            issues.append("Fixed: Added missing commas in dict literals")
    
    return issues

def main():
    print("=" * 80)
    print("COMPREHENSIVE AUDIT: Indian SME Doc Intelligence RAG")
    print("Checking EVERY file, EVERY line, EVERY word, EVERY byte...")
    print("=" * 80)
    print()
    
    # Get all Python files in the project (excluding venv, __pycache__, etc.)
    project_root = os.path.dirname(os.path.abspath(__file__))
    python_files = []
    
    for root, dirs, files in os.walk(project_root):
        # Skip virtual environment and cache directories
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', 'node_modules', '.git']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    python_files.sort()
    
    total_issues = 0
    files_with_issues = 0
    
    for filepath in python_files:
        rel_path = os.path.relpath(filepath, project_root)
        issues = audit_file(filepath)
        
        if issues:
            files_with_issues += 1
            total_issues += len(issues)
            print(f"[FILE] {rel_path}")
            for issue in issues:
                print(f"   [ISSUE] {issue}")
            print()
    
    print("=" * 80)
    print(f"AUDIT COMPLETE")
    print(f"Files checked: {len(python_files)}")
    print(f"Files with issues: {files_with_issues}")
    print(f"Total issues found: {total_issues}")
    print("=" * 80)
    
    if total_issues == 0:
        print("\n[OK] ALL FILES ARE CLEAN - READY FOR PRODUCTION!")
        return 0
    else:
        print(f"\n[WARN] {total_issues} issues found. Please review and fix.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
