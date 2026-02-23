"""
Seed script to add comprehensive list of world countries to the database.
Covers all major countries across all continents with realistic pricing.
"""
import asyncio
from backend.database import async_session, engine
from backend.models import Base, Country
from sqlalchemy import select

# Comprehensive list of countries by continent with emoji and price
COUNTRIES = [
    # Asia
    {"name": "India", "emoji": "🇮🇳", "price": 35.0},
    {"name": "Pakistan", "emoji": "🇵🇰", "price": 30.0},
    {"name": "Bangladesh", "emoji": "🇧🇩", "price": 25.0},
    {"name": "China", "emoji": "🇨🇳", "price": 50.0},
    {"name": "Japan", "emoji": "🇯🇵", "price": 80.0},
    {"name": "South Korea", "emoji": "🇰🇷", "price": 70.0},
    {"name": "Indonesia", "emoji": "🇮🇩", "price": 40.0},
    {"name": "Malaysia", "emoji": "🇲🇾", "price": 45.0},
    {"name": "Singapore", "emoji": "🇸🇬", "price": 90.0},
    {"name": "Thailand", "emoji": "🇹🇭", "price": 35.0},
    {"name": "Vietnam", "emoji": "🇻🇳", "price": 30.0},
    {"name": "Philippines", "emoji": "🇵🇭", "price": 30.0},
    {"name": "UAE", "emoji": "🇦🇪", "price": 75.0},
    {"name": "Saudi Arabia", "emoji": "🇸🇦", "price": 70.0},
    {"name": "Turkey", "emoji": "🇹🇷", "price": 45.0},
    {"name": "Israel", "emoji": "🇮🇱", "price": 65.0},
    
    # Europe
    {"name": "United Kingdom", "emoji": "🇬🇧", "price": 85.0},
    {"name": "Germany", "emoji": "🇩🇪", "price": 80.0},
    {"name": "France", "emoji": "🇫🇷", "price": 75.0},
    {"name": "Italy", "emoji": "🇮🇹", "price": 70.0},
    {"name": "Spain", "emoji": "🇪🇸", "price": 65.0},
    {"name": "Netherlands", "emoji": "🇳🇱", "price": 75.0},
    {"name": "Belgium", "emoji": "🇧🇪", "price": 70.0},
    {"name": "Switzerland", "emoji": "🇨🇭", "price": 95.0},
    {"name": "Austria", "emoji": "🇦🇹", "price": 70.0},
    {"name": "Poland", "emoji": "🇵🇱", "price": 50.0},
    {"name": "Russia", "emoji": "🇷🇺", "price": 55.0},
    {"name": "Ukraine", "emoji": "🇺🇦", "price": 40.0},
    {"name": "Sweden", "emoji": "🇸🇪", "price": 75.0},
    {"name": "Norway", "emoji": "🇳🇴", "price": 85.0},
    {"name": "Denmark", "emoji": "🇩🇰", "price": 80.0},
    {"name": "Finland", "emoji": "🇫🇮", "price": 75.0},
    {"name": "Czech Republic", "emoji": "🇨🇿", "price": 55.0},
    {"name": "Portugal", "emoji": "🇵🇹", "price": 60.0},
    {"name": "Greece", "emoji": "🇬🇷", "price": 55.0},
    
    # North America
    {"name": "United States", "emoji": "🇺🇸", "price": 100.0},
    {"name": "Canada", "emoji": "🇨🇦", "price": 90.0},
    {"name": "Mexico", "emoji": "🇲🇽", "price": 40.0},
    
    # South America
    {"name": "Brazil", "emoji": "🇧🇷", "price": 45.0},
    {"name": "Argentina", "emoji": "🇦🇷", "price": 40.0},
    {"name": "Chile", "emoji": "🇨🇱", "price": 50.0},
    {"name": "Colombia", "emoji": "🇨🇴", "price": 35.0},
    {"name": "Peru", "emoji": "🇵🇪", "price": 35.0},
    {"name": "Venezuela", "emoji": "🇻🇪", "price": 30.0},
    
    # Africa
    {"name": "South Africa", "emoji": "🇿🇦", "price": 45.0},
    {"name": "Nigeria", "emoji": "🇳🇬", "price": 35.0},
    {"name": "Egypt", "emoji": "🇪🇬", "price": 40.0},
    {"name": "Kenya", "emoji": "🇰🇪", "price": 35.0},
    {"name": "Morocco", "emoji": "🇲🇦", "price": 40.0},
    {"name": "Ghana", "emoji": "🇬🇭", "price": 35.0},
    
    # Oceania
    {"name": "Australia", "emoji": "🇦🇺", "price": 90.0},
    {"name": "New Zealand", "emoji": "🇳🇿", "price": 85.0},
]

async def seed_countries():
    """Add countries to database (skip if already exists)"""
    async with async_session() as session:
        async with session.begin():
            # Create tables if they don't exist
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            added = 0
            skipped = 0
            
            for country_data in COUNTRIES:
                # Check if country already exists
                stmt = select(Country).where(Country.name == country_data["name"])
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    print(f"⏭️  Skipping {country_data['emoji']} {country_data['name']} (already exists)")
                    skipped += 1
                else:
                    country = Country(**country_data)
                    session.add(country)
                    print(f"✅ Added {country_data['emoji']} {country_data['name']} (₹{country_data['price']})")
                    added += 1
            
            await session.commit()
            
            print(f"\n{'='*60}")
            print(f"✨ Country Seed Complete!")
            print(f"✅ Added: {added} countries")
            print(f"⏭️  Skipped: {skipped} countries (already exist)")
            print(f"📊 Total: {len(COUNTRIES)} countries processed")
            print(f"{'='*60}")

if __name__ == "__main__":
    print("🌍 Seeding World Countries Database...")
    print(f"{'='*60}\n")
    asyncio.run(seed_countries())
