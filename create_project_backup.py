import os
import zipfile

def zip_project(output_filename="telegram_bot_full_backup.zip"):
    # Get current directory
    root_dir = os.getcwd()
    
    # Folders to exclude
    EXCLUDE_DIRS = {
        'node_modules', 
        '.git', 
        '__pycache__', 
        '.venv', 
        'venv', 
        '.idea', 
        '.vscode',
        'dist',
        'build',
        '.gemini' # Exclude the agent artifact directory
    }
    
    # Files to exclude
    EXCLUDE_FILES = {
        output_filename,
        '.DS_Store',
        'Thumbs.db'
    }

    print(f"📦 Creating backup: {output_filename}...")
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(root_dir):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                if file in EXCLUDE_FILES:
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, root_dir)
                
                # Double check against exclude dirs in path
                parts = arcname.split(os.sep)
                if any(part in EXCLUDE_DIRS for part in parts):
                    continue

                try:
                    # print(f"  Adding: {arcname}") # Commented out to reduce noise
                    zipf.write(file_path, arcname)
                except Exception as e:
                    print(f"⚠️ Could not add {arcname}: {e}")

    print(f"\n✅ Backup created successfully: {os.path.join(root_dir, output_filename)}")
    print(f"📊 Size: {os.path.getsize(output_filename) / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    zip_project()
