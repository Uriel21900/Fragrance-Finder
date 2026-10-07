"""
hourly_fragrance_check.py
Audits the database hourly to verify that new fragrances and discounter price
observations are actively being captured and stored in Neon DB.
"""

import os
import sys
import asyncio
import datetime

# Safe stdout UTF-8 configuration
if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8', errors='replace')

import asyncpg
from dotenv import load_dotenv

load_dotenv("backend/.env")
load_dotenv(".env")

FALLBACK_DATABASE_URL = "postgresql://neondb_owner:npg_iN45StWGXmpK@ep-winter-surf-ay718z8s-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"

def get_db_url() -> str:
    raw = os.getenv("DATABASE_URL")
    if not raw or not raw.strip() or not raw.strip().startswith("postgres"):
        return FALLBACK_DATABASE_URL
    return raw.strip().strip("'").strip('"')

async def run_hourly_check():
    now = datetime.datetime.now(datetime.timezone.utc)
    one_hour_ago = now - datetime.timedelta(hours=1)
    six_hours_ago = now - datetime.timedelta(hours=6)
    twenty_four_hours_ago = now - datetime.timedelta(hours=24)
    
    db_url = get_db_url()
    conn = await asyncpg.connect(db_url)
    
    try:
        total_fragrances = await conn.fetchval("SELECT count(*) FROM fragrance_dna;")
        total_prices = await conn.fetchval("SELECT count(*) FROM price_observation;")
        
        # New observations within time windows
        prices_last_1h = await conn.fetchval(
            "SELECT count(*) FROM price_observation WHERE observed_at >= $1;",
            one_hour_ago
        )
        prices_last_6h = await conn.fetchval(
            "SELECT count(*) FROM price_observation WHERE observed_at >= $1;",
            six_hours_ago
        )
        prices_last_24h = await conn.fetchval(
            "SELECT count(*) FROM price_observation WHERE observed_at >= $1;",
            twenty_four_hours_ago
        )
        
        # Distinct fragrances with prices
        fragrances_with_prices = await conn.fetchval("""
            SELECT count(DISTINCT l.dna_id)
            FROM fragrance_line l
            JOIN fragrance_product fp ON l.line_id = fp.line_id
            JOIN product_variant pv ON fp.product_id = pv.product_id
            JOIN price_observation p ON pv.variant_id = p.variant_id;
        """)
        
        # Latest 5 price observations with brand and fragrance name
        latest_rows = await conn.fetch("""
            SELECT 
                b.name AS brand_name,
                d.canonical_name AS fragrance_name,
                r.name AS retailer_name,
                p.price_amount,
                p.observed_at,
                p.source_url
            FROM price_observation p
            JOIN product_variant pv ON p.variant_id = pv.variant_id
            JOIN fragrance_product fp ON pv.product_id = fp.product_id
            JOIN fragrance_line l ON fp.line_id = l.line_id
            JOIN fragrance_dna d ON l.dna_id = d.dna_id
            LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
            LEFT JOIN retailer r ON p.retailer_id = r.retailer_id
            ORDER BY p.observed_at DESC
            LIMIT 5;
        """)
        
        report: list[str] = []
        report.append("=" * 70)
        report.append(f"⏱️ HOURLY FRAGRANCE AUDIT REPORT: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append("=" * 70)
        report.append(f"📊 Catalog Fragrance DNA Total : {total_fragrances}")
        report.append(f"💎 Fragrances with Live Prices : {fragrances_with_prices} ({(fragrances_with_prices/total_fragrances*100):.1f}%)")
        report.append(f"🏷️ Total Price Observations   : {total_prices}")
        report.append(f"📈 Added in Last 1 Hour       : {prices_last_1h} new price updates")
        report.append(f"📈 Added in Last 6 Hours      : {prices_last_6h} new price updates")
        report.append(f"📈 Added in Last 24 Hours     : {prices_last_24h} new price updates")
        report.append("-" * 70)
        report.append("🔥 Latest Live Price Observations:")
        for r in latest_rows:
            brand = r['brand_name'] or "Unknown"
            frag = r['fragrance_name'] or "Unknown"
            ret = r['retailer_name'] or "Unknown"
            price = f"${float(r['price_amount']):.2f}"
            t_str = r['observed_at'].strftime("%H:%M:%S")
            report.append(f"   [{t_str}] {price:>8} | {ret:<18} | {brand} - {frag}")
        report.append("=" * 70)
        
        full_report_text = "\n".join(report)
        print(full_report_text)
        
        # Save to log file
        log_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "hourly_audit.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(full_report_text + "\n\n")
            
        return {
            "total_fragrances": total_fragrances,
            "total_prices": total_prices,
            "prices_last_1h": prices_last_1h,
            "is_active": prices_last_1h > 0 or prices_last_6h > 0
        }
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_hourly_check())
