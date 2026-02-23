"""
Script to create /admin/settings/payment endpoint for channel and owner settings
"""

# Add this to backend/main.py after the other admin routes

endpoint_code = '''
@app.get("/admin/settings/payment")
async def get_payment_settings():
    """Fetch current payment settings and bot config"""
    async with async_session() as session:
        upi_res = await session.execute(select(Settings).where(Settings.key == "payment_upi_id"))
        qr_res = await session.execute(select(Settings).where(Settings.key == "payment_qr_image"))
        channel_res = await session.execute(select(Settings).where(Settings.key == "bot_channel_link"))
        owner_res = await session.execute(select(Settings).where(Settings.key == "bot_owner_username"))
        
        upi_id = upi_res.scalar_one_or_none()
        qr_image = qr_res.scalar_one_or_none()
        channel_link = channel_res.scalar_one_or_none()
        owner_username = owner_res.scalar_one_or_none()
        
        return {
            "upi_id": upi_id.value if upi_id else "",
            "qr_image": qr_image.value if qr_image else "",
            "channel_link": channel_link.value if channel_link else "",
            "owner_username": owner_username.value if owner_username else ""
        }

@app.post("/admin/settings/payment")
async def update_payment_settings(
    upi_id: str = Form(""),
    qr_image: UploadFile = File(None),
    channel_link: str = Form(""),
    owner_username: str = Form("")
):
    """Update payment settings and bot configuration"""
    async with async_session() as session:
        # Update or create UPI ID
        upi_stmt = select(Settings).where(Settings.key == "payment_upi_id")
        upi_res = await session.execute(upi_stmt)
        upi_setting = upi_res.scalar_one_or_none()
        
        if upi_setting:
            upi_setting.value = upi_id
        else:
            session.add(Settings(key="payment_upi_id", value=upi_id))
        
        # Update or create channel link
        channel_stmt = select(Settings).where(Settings.key == "bot_channel_link")
        channel_res = await session.execute(channel_stmt)
        channel_setting = channel_res.scalar_one_or_none()
        
        if channel_setting:
            channel_setting.value = channel_link
        else:
            session.add(Settings(key="bot_channel_link", value=channel_link))
        
        # Update or create owner username
        owner_stmt = select(Settings).where(Settings.key == "bot_owner_username")
        owner_res = await session.execute(owner_stmt)
        owner_setting = owner_res.scalar_one_or_none()
        
        if owner_setting:
            owner_setting.value = owner_username
        else:
            session.add(Settings(key="bot_owner_username", value=owner_username))
        
        # Handle QR image upload if provided
        if qr_image and qr_image.filename:
            contents = await qr_image.read()
            base64_encoded = base64.b64encode(contents).decode('utf-8')
            data_uri = f"data:{qr_image.content_type};base64,{base64_encoded}"
            
            qr_stmt = select(Settings).where(Settings.key == "payment_qr_image")
            qr_res = await session.execute(qr_stmt)
            qr_setting = qr_res.scalar_one_or_none()
            
            if qr_setting:
                qr_setting.value = data_uri
            else:
                session.add(Settings(key="payment_qr_image", value=data_uri))
        
        await session.commit()
        return {"status": "success"}
'''

print("Copy this code and add it to backend/main.py around line 270:")
print("="*60)
print(endpoint_code)
print("="*60)
