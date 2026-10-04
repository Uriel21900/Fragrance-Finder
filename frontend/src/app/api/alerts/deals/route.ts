import { NextResponse } from 'next/server';
import { sql } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const deals = await sql`
      SELECT 
        d.dna_id,
        d.canonical_name,
        d.image_url,
        d.gender,
        d.market_segment,
        b.name as brand_name,
        p.price_amount as sale_price,
        p.source_url,
        r.name as retailer_name
      FROM price_observation p
      JOIN product_variant v ON p.variant_id = v.variant_id
      JOIN fragrance_product fp ON v.product_id = fp.product_id
      JOIN fragrance_line l ON fp.line_id = l.line_id
      JOIN fragrance_dna d ON l.dna_id = d.dna_id
      LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
      LEFT JOIN retailer r ON p.retailer_id = r.retailer_id
      ORDER BY p.captured_at DESC
      LIMIT 12
    `;

    const formatted = deals.map((row: any) => ({
      fragrance: {
        dna_id: row.dna_id,
        brand_name: row.brand_name || 'Brand',
        canonical_name: row.canonical_name,
        image_url: row.image_url,
        gender: row.gender,
        market_segment: row.market_segment
      },
      retailer_name: row.retailer_name || 'Retailer',
      original_price: parseFloat(row.sale_price) * 1.25,
      sale_price: parseFloat(row.sale_price),
      source_url: row.source_url
    }));

    return NextResponse.json(formatted);
  } catch (error: any) {
    console.error('Error fetching deals:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
