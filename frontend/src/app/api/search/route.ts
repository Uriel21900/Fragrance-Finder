import { NextResponse } from 'next/server';
import { sql } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const q = searchParams.get('q') || '';
  const brand = searchParams.get('brand') || '';
  // Only include inspired_by matches when the caller explicitly opts in
  // (e.g. a "Find clones of X" feature). Default OFF to prevent
  // cross-contamination where searching "Layton" returns clones of Layton
  // instead of Layton itself.
  const includeInspiredBy = searchParams.get('include_inspired_by') === 'true';

  try {
    let dnas = [];
    const searchPattern = `%${q.trim()}%`;
    const exactName = q.trim();

    if (q && brand) {
      dnas = await sql`
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
          d.gender,
          b.name as brand_name
        FROM fragrance_dna d
        LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
        WHERE (
            d.canonical_name ILIKE ${searchPattern}
            OR b.name ILIKE ${searchPattern}
            ${includeInspiredBy ? sql`OR d.inspired_by ILIKE ${searchPattern}` : sql``}
          )
          AND b.name ILIKE ${'%' + brand + '%'}
        ORDER BY
          CASE WHEN LOWER(d.canonical_name) = LOWER(${exactName}) THEN 0
               WHEN d.canonical_name ILIKE ${searchPattern}        THEN 1
               ELSE 2
          END,
          d.canonical_name
        LIMIT 24
      `;
    } else if (q) {
      dnas = await sql`
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
          d.gender,
          b.name as brand_name
        FROM fragrance_dna d
        LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
        WHERE d.canonical_name ILIKE ${searchPattern}
           OR b.name ILIKE ${searchPattern}
           ${includeInspiredBy ? sql`OR d.inspired_by ILIKE ${searchPattern}` : sql``}
        ORDER BY
          CASE WHEN LOWER(d.canonical_name) = LOWER(${exactName}) THEN 0
               WHEN d.canonical_name ILIKE ${searchPattern}        THEN 1
               ELSE 2
          END,
          d.canonical_name
        LIMIT 24
      `;
    } else if (brand) {
      dnas = await sql`
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
          d.gender,
          b.name as brand_name
        FROM fragrance_dna d
        LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
        WHERE b.name ILIKE ${'%' + brand + '%'}
        ORDER BY d.canonical_name
        LIMIT 24
      `;
    } else {
      return NextResponse.json([]);
    }

    const dnaIds = dnas.map((d: any) => d.dna_id);
    if (dnaIds.length === 0) {
      return NextResponse.json([]);
    }

    // Fetch prices
    const priceRows = await sql`
      SELECT 
        l.dna_id,
        v.variant_id,
        p.price_amount,
        p.currency_code,
        p.source_url,
        r.name as retailer_name
      FROM fragrance_line l
      JOIN fragrance_product fp ON l.line_id = fp.line_id
      JOIN product_variant v ON fp.product_id = v.product_id
      JOIN price_observation p ON v.variant_id = p.variant_id
      LEFT JOIN retailer r ON p.retailer_id = r.retailer_id
      WHERE l.dna_id = ANY(${dnaIds})
    `;

    const pricesByDna: Record<string, any[]> = {};
    for (const row of priceRows) {
      if (!pricesByDna[row.dna_id]) {
        pricesByDna[row.dna_id] = [];
      }
      pricesByDna[row.dna_id].push({
        retailer_name: row.retailer_name || 'Retailer',
        price_amount: parseFloat(row.price_amount),
        currency_code: row.currency_code,
        source_url: row.source_url
      });
    }

    const responses = dnas.map((dna: any) => {
      const prices = pricesByDna[dna.dna_id] || [];
      return {
        dna_id: dna.dna_id,
        brand_name: dna.brand_name || 'Unknown Brand',
        canonical_name: dna.canonical_name,
        market_segment: dna.market_segment,
        gender: dna.gender,
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
        ]
      };
    });

    return NextResponse.json(responses);
  } catch (error: any) {
    console.error('Error during search:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
