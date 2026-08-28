import { NextResponse } from 'next/server';
import { sql } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: Request, { params }: { params: { id: string } }) {
  const { id } = params;

  try {
    // 1. Fetch Fragrance DNA
    const dnas = await sql`
      SELECT 
        d.dna_id,
        d.canonical_name,
        d.normalized_name,
        d.market_segment,
        d.first_release_year,
        d.is_dupe,
        d.inspired_by,
        d.influencer_mentions,
        d.image_url,
        b.name as brand_name
      FROM fragrance_dna d
      LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
      WHERE d.dna_id = ${id}
    `;

    if (dnas.length === 0) {
      return NextResponse.json({ error: 'Fragrance not found' }, { status: 404 });
    }

    const dna = dnas[0];

    // 2. Fetch prices
    const priceRows = await sql`
      SELECT 
        v.variant_id,
        v.volume_ml,
        v.package_type,
        p.price_observation_id,
        p.price_amount,
        p.currency_code,
        p.source_url,
        p.captured_at,
        r.name as retailer_name
      FROM fragrance_line l
      JOIN fragrance_product fp ON l.line_id = fp.line_id
      JOIN product_variant v ON fp.product_id = v.product_id
      JOIN price_observation p ON v.variant_id = p.variant_id
      LEFT JOIN retailer r ON p.retailer_id = r.retailer_id
      WHERE l.dna_id = ${id}
      ORDER BY p.price_amount ASC
    `;

    // Deduplicate prices per retailer and source_url
    const latestPrices = new Map();
    for (const row of priceRows) {
      let rName = row.retailer_name;
      if (!rName || rName === 'Unknown') {
        if (row.source_url) {
          try {
            const urlObj = new URL(row.source_url);
            rName = urlObj.hostname.replace('www.', '');
          } catch {
            rName = 'Retailer';
          }
        } else {
          rName = 'Retailer';
        }
      }
      const key = `${rName}-${row.source_url}`;
      if (!latestPrices.has(key) || new Date(row.captured_at) > new Date(latestPrices.get(key).captured_at)) {
        latestPrices.set(key, {
          price_observation_id: row.price_observation_id,
          retailer_name: rName,
          price_amount: parseFloat(row.price_amount),
          currency_code: row.currency_code,
          source_url: row.source_url,
          captured_at: row.captured_at,
          volume_ml: row.volume_ml ? parseFloat(row.volume_ml) : 100,
          package_type: row.package_type || 'spray'
        });
      }
    }

    const prices = Array.from(latestPrices.values()).sort((a, b) => a.price_amount - b.price_amount);

    // 3. Fetch clones / inspired by
    const cloneRows = await sql`
      SELECT 
        d.dna_id,
        d.canonical_name,
        d.image_url,
        b.name as brand_name
      FROM dna_relationship rel
      JOIN fragrance_dna d ON rel.source_dna_id = d.dna_id
      LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
      WHERE rel.target_dna_id = ${id}
    `;

    const clones = cloneRows.map((c: any) => ({
      dna_id: c.dna_id,
      brand_name: c.brand_name || 'Unknown Brand',
      canonical_name: c.canonical_name,
      image_url: c.image_url
    }));

    const response = {
      dna_id: dna.dna_id,
      brand_name: dna.brand_name || 'Unknown Brand',
      canonical_name: dna.canonical_name,
      market_segment: dna.market_segment,
      first_release_year: dna.first_release_year,
      is_dupe: dna.is_dupe,
      inspired_by: dna.inspired_by,
      influencer_mentions: dna.influencer_mentions,
      image_url: dna.image_url,
      variants: [
        {
          variant_id: dna.dna_id,
          volume_ml: 100,
          package_type: 'spray',
          prices: prices
        }
      ],
      clones: clones
    };

    return NextResponse.json(response);
  } catch (error: any) {
    console.error('Error fetching fragrance detail:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
