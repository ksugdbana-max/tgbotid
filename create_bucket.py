import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("❌ Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

try:
    print(f"Connecting to {url}...")
    supabase: Client = create_client(url, key)
    
    bucket_name = "bot-uploads"
    
    print(f"Attempting to create bucket: '{bucket_name}'...")
    # Create bucket - public=True is important for images to be viewable
    res = supabase.storage.create_bucket(bucket_name, options={"public": True})
    
    print(f"✅ Success! Bucket '{bucket_name}' created.")
    print(f"Response: {res}")

except Exception as e:
    print(f"❌ Failed to create bucket: {e}")
    # Check if it already exists
    try:
        buckets = supabase.storage.list_buckets()
        print("Existing buckets:", [b.name for b in buckets])
    except:
        pass
