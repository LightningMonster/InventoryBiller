
import os
import shutil
from pathlib import Path

# Create required directories
build_dir = Path('build/BillingSystem')
build_dir.mkdir(parents=True, exist_ok=True)

# Create app directories 
for dir_name in ['database', 'bills', 'logs']:
    (build_dir / dir_name).mkdir(exist_ok=True)

# Copy source files
src_dir = Path('src')
dest_dir = build_dir / 'src'
dest_dir.mkdir(exist_ok=True)

for file in src_dir.glob('*.py'):
    shutil.copy2(file, dest_dir)

# Copy assets
if Path('assets').exists():
    shutil.copytree('assets', build_dir / 'assets', dirs_exist_ok=True)

print("Build structure created successfully!")
print(f"You can find the built application in: {build_dir}")
