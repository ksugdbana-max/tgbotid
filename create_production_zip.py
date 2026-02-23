import zipfile
import os

# Create zip file
zip_filename = 'telegram-bot-production.zip'
z = zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED)

# Essential backend files
backend_files = [
    'backend/main.py',
    'backend/bot.py',
    'backend/database.py',
    'backend/models.py',
    'backend/session_manager.py',
    'backend/device_manager.py',
    'backend/session_generator_service.py',
    'backend/otp_handlers.py',
    'backend/requirements.txt',
    'backend/__init__.py',
]

# Add backend files
for file in backend_files:
    if os.path.exists(file):
        z.write(file, file)
        print(f"✓ Added {file}")

# Add entire frontend directory
for root, dirs, files in os.walk('frontend'):
    # Skip node_modules and dist
    if 'node_modules' in root or 'dist' in root or '.vercel' in root:
        continue
    for file in files:
        file_path = os.path.join(root, file)
        z.write(file_path, file_path)
        print(f"✓ Added {file_path}")

# Essential root files
root_files = [
    'Dockerfile',
    'Procfile',
    '.gitignore',
    'deploy.env',
]

for file in root_files:
    if os.path.exists(file):
        z.write(file, file)
        print(f"✓ Added {file}")

z.close()
print(f"\n✅ Created {zip_filename}")
print(f"📦 Location: {os.path.abspath(zip_filename)}")
