from pyngrok import ngrok
import time
import os

# Set auth token
ngrok.set_auth_token('37r4Tz8rzuT1tewsQUlDYzNd2dt_4EFVdvDiDckZZqxYkaHnn')

# Start single tunnel for FastAPI (which now serves frontend too)
public_url = ngrok.connect(8000, "http").public_url
print(f"NGROK_URL: {public_url}")

# Save to file
with open("ngrok_url.txt", "w") as f:
    f.write(public_url)

# Update .env
env_path = ".env"
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        lines = f.readlines()
    
    with open(env_path, "w") as f:
        for line in lines:
            if line.startswith("ADMIN_WEBAPP_URL="):
                f.write(f"ADMIN_WEBAPP_URL={public_url}\n")
            else:
                f.write(line)

# Keep alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ngrok.disconnect(public_url)
