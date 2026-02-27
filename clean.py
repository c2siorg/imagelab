import os
import re

files_to_clean = [
    'imagelab-frontend/vite.config.ts',
    'imagelab-frontend/tests/blocklyMockFactory.ts',
    'imagelab-frontend/tests/extractPipeline.test.ts'
]

def clean_file(path):
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Strip invisible bidi/control characters (e.g. U+200B - U+200F, U+2028 - U+202F, etc)
    # Actually, we can just allow printable ASCII + standard whitespace
    clean_content = re.sub(r'[^\x20-\x7E\t\n\r]+', '', content)
    
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(clean_content)
    print(f"Cleaned {path}")

for f in files_to_clean:
    clean_file(f)
