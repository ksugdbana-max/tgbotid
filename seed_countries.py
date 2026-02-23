"""
Comprehensive Country List for Telegram ID Bot
Seeds database with all major countries and their emojis
"""
import asyncio
from backend.database import async_session
from backend.models import Country
from sqlalchemy import select

# Comprehensive country list with emojis and suggested prices
COUNTRIES = [
    # Asia
    {"name": "India", "emoji": "🇮🇳", "price": 26.0},
    {"name": "Pakistan", "emoji": "🇵🇰", "price": 28.0},
    {"name": "Bangladesh", "emoji": "🇧🇩", "price": 25.0},
    {"name": "Indonesia", "emoji": "🇮🇩", "price": 30.0},
    {"name": "Malaysia", "emoji": "🇲🇾", "price": 35.0},
    {"name": "Philippines", "emoji": "🇵🇭", "price": 32.0},
    {"name": "Thailand", "emoji": "🇹🇭", "price": 38.0},
    {"name": "Vietnam", "emoji": "🇻🇳", "price": 35.0},
    {"name": "Singapore", "emoji": "🇸🇬", "price": 50.0},
    {"name": "Japan", "emoji": "🇯🇵", "price": 60.0},
    {"name": "South Korea", "emoji": "🇰🇷", "price": 55.0},
    {"name": "China", "emoji": "🇨🇳", "price": 45.0},
    {"name": "Taiwan", "emoji": "🇹🇼", "price": 48.0},
    {"name": "Hong Kong", "emoji": "🇭🇰", "price": 52.0},
    
    # Middle East
    {"name": "UAE", "emoji": "🇦🇪", "price": 55.0},
    {"name": "Saudi Arabia", "emoji": "🇸🇦", "price": 50.0},
    {"name": "Qatar", "emoji": "🇶🇦", "price": 52.0},
    {"name": "Kuwait", "emoji": "🇰🇼", "price": 48.0},
    {"name": "Turkey", "emoji": "🇹🇷", "price": 35.0},
    {"name": "Israel", "emoji": "🇮🇱", "price": 45.0},
    {"name": "Iran", "emoji": "🇮🇷", "price": 30.0},
    {"name": "Iraq", "emoji": "🇮🇶", "price": 32.0},
    
    # Europe
    {"name": "United Kingdom", "emoji": "🇬🇧", "price": 60.0},
    {"name": "Germany", "emoji": "🇩🇪", "price": 55.0},
    {"name": "France", "emoji": "🇫🇷", "price": 55.0},
    {"name": "Italy", "emoji": "🇮🇹", "price": 50.0},
    {"name": "Spain", "emoji": "🇪🇸", "price": 48.0},
    {"name": "Netherlands", "emoji": "🇳🇱", "price": 52.0},
    {"name": "Belgium", "emoji": "🇧🇪", "price": 50.0},
    {"name": "Switzerland", "emoji": "🇨🇭", "price": 65.0},
    {"name": "Austria", "emoji": "🇦🇹", "price": 52.0},
    {"name": "Poland", "emoji": "🇵🇱", "price": 40.0},
    {"name": "Ukraine", "emoji": "🇺🇦", "price": 35.0},
    {"name": "Russia", "emoji": "🇷🇺", "price": 38.0},
    {"name": "Sweden", "emoji": "🇸🇪", "price": 55.0},
    {"name": "Norway", "emoji": "🇳🇴", "price": 60.0},
    {"name": "Denmark", "emoji": "🇩🇰", "price": 55.0},
    {"name": "Finland", "emoji": "🇫🇮", "price": 52.0},
    {"name": "Portugal", "emoji": "🇵🇹", "price": 45.0},
    {"name": "Greece", "emoji": "🇬🇷", "price": 42.0},
    
    # Americas
    {"name": "USA", "emoji": "🇺🇸", "price": 70.0},
    {"name": "Canada", "emoji": "🇨🇦", "price": 65.0},
    {"name": "Mexico", "emoji": "🇲🇽", "price": 38.0},
    {"name": "Brazil", "emoji": "🇧🇷", "price": 35.0},
    {"name": "Argentina", "emoji": "🇦🇷", "price": 32.0},
    {"name": "Chile", "emoji": "🇨🇱", "price": 35.0},
    {"name": "Colombia", "emoji": "🇨🇴", "price": 30.0},
    {"name": "Peru", "emoji": "🇵🇪", "price": 28.0},
    
    # Africa
    {"name": "South Africa", "emoji": "🇿🇦", "price": 35.0},
    {"name": "Nigeria", "emoji": "🇳🇬", "price": 28.0},
    {"name": "Kenya", "emoji": "🇰🇪", "price": 30.0},
    {"name": "Egypt", "emoji": "🇪🇬", "price": 32.0},
    {"name": "Morocco", "emoji": "🇲🇦", "price": 30.0},
    {"name": "Algeria", "emoji": "🇩🇿", "price": 28.0},
    {"name": "Tunisia", "emoji": "🇹🇳", "price": 28.0},
    
    # Oceania
    {"name": "Australia", "emoji": "🇦🇺", "price": 65.0},
    {"name": "New Zealand", "emoji": "🇳🇿", "price": 60.0},
]


async def seed_countries():
    """Add all countries to database"""
    async with async_session() as session:
        # Get existing countries
        stmt = select(Country)
        result = await session.execute(stmt)
        existing = {c.name: c for c in result.scalars().all()}
        
        added = 0
        updated = 0
        
        for country_data in COUNTRIES:
            if country_data["name"] in existing:
                # Update existing
                country = existing[country_data["name"]]
                country.emoji = country_data["emoji"]
                # Don't override price if already set
                updated += 1
            else:
                # Add new
                country = Country(**country_data)
                session.add(country)
                added += 1
        
        await session.commit()
        
        print(f"✅ Countries seeded successfully!")
        print(f"   Added: {added} new countries")
        print(f"   Updated: {updated} existing countries")
        print(f"   Total: {len(COUNTRIES)} countries in list")


if __name__ == "__main__":
    asyncio.run(seed_countries())
