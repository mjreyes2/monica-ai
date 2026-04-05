import os
import re

def update_imports(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # This regex is a simple example and might need to be adjusted
                # for more complex import statements.
                content = re.sub(r'from (monica_[\w_]+) import', r'from services.\1 import', content)
                content = re.sub(r'from (train_[\w_]+) import', r'from models.\1 import', content)
                content = re.sub(r'from (monica_[\w_]+) import', r'from core.\1 import', content)

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

if __name__ == '__main__':
    update_imports('src')
    update_imports('tests')
