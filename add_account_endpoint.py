"""
Add Account Creation Endpoint
This creates the missing /admin/accounts POST endpoint
"""

# Add this code to backend/main.py

from pydantic import BaseModel

class AccountCreate(BaseModel):
    country_id: int
    phone_number: str
    session_data: str
    type: str = "ID"
    twofa_password: str = None

@app.post("/admin/accounts")
async def create_account(account: AccountCreate):
    """Create a new account - allows duplicates after sold"""
    async with async_session() as session:
        # Create new account (no duplicate check - allows restocking)
        new_account = Account(
            country_id=account.country_id,
            phone_number=account.phone_number,
            session_data=account.session_data,
            type=account.type,
            twofa_password=account.twofa_password,
            is_sold=False
        )
        
        session.add(new_account)
        await session.commit()
        await session.refresh(new_account)
        
        return {
            "success": True,
            "message": "Account added successfully",
            "account": {
                "id": new_account.id,
                "phone_number": new_account.phone_number,
                "country_id": new_account.country_id
            }
        }
