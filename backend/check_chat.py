import sys
with open('app/schemas/chat.py', 'rb') as f:
    content = f.read()

lines = content.split(b'\n')
print('Total lines:', len(lines))

# Check line 25 (index 24)
if len(lines) > 24:
    line25 = lines[24]
    print('Line 25 bytes:', line25)
    print('Line 25 repr:', repr(line25))
    
    # Check for non-ASCII
    for i, b in enumerate(line25):
        if b > 127:
            print(f'  Non-ASCII at position {i}: {b}')
