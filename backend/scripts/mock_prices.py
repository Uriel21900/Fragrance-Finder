import asyncio
import os
import sys
import random
import uuid
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import ProductVariant, Retailer, PriceObservation
from sqlalchemy import select

async def mock_prices():
    async with async_session_maker() as session:
        # 1. Add retailers
        res = await session.execute(select(Retailer))
        retailers = res.scalars().all()
        if not retailers:
            names = ['Jomashop', 'Macys', 'FragranceNet', 'AuraFragrance', 'Sephora']
            for name in names:
                session.add(Retailer(name=name, website_url=f'https://{name.lower()}.com', normalized_name=name.lower()))
            await session.commit()
            res = await session.execute(select(Retailer))
            retailers = res.scalars().all()
            
        print(f'Found {len(retailers)} retailers')

        # 2. Add mock prices for ALL variants missing prices
        res = await session.execute(
            select(ProductVariant.variant_id)
            .outerjoin(PriceObservation)
            .where(PriceObservation.price_observation_id == None)
        )
        variant_ids = [row[0] for row in res.all()]
        print(f'Found {len(variant_ids)} variants missing prices. Mocking...')
        
        batch_size = 1000
        count = 0
        for i in range(0, len(variant_ids), batch_size):
            batch = variant_ids[i:i+batch_size]
            for v_id in batch:
                num_prices = min(random.randint(1, 3), len(retailers))
                selected_retailers = random.sample(retailers, num_prices)
                base_price = random.uniform(40.0, 350.0)
                
                for r in selected_retailers:
                    price_val = base_price * random.uniform(0.85, 1.15)
                    url_str = r.website_url if r.website_url else "https://example.com"
                    obs = PriceObservation(
                        variant_id=v_id,
                        retailer_id=r.retailer_id,
                        price_amount=round(price_val, 2),
                        currency_code='USD',
                        source_url=f"{url_str}/product/{uuid.uuid4()}",
                        captured_at=datetime.now(timezone.utc)
                    )
                    session.add(obs)
                    count += 1
            await session.commit()
            print(f'Inserted price batch {i//batch_size + 1}. Total: {count}')

if __name__ == "__main__":
    asyncio.run(mock_prices())
