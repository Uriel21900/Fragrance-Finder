import { NextResponse } from 'next/server';
import { sql } from '@/lib/db';
import { isStrictMatch, cleanSourceUrl } from '@/lib/strict-matcher';

export const dynamic = 'force-dynamic';

const FEATURED_POPULAR_NAMES = [
  'Aventus',
  'Baccarat Rouge 540',
  "Angels' Share",
  'Layton',
  'Tobacco Vanille',
  'Sauvage Elixir',
  'Detour Noir',
  'Club De Nuit Intense Man',
  'Khamrah',
  'Asad',
  '9pm',
  'The Tux',
  'Club De Nuit Untold'
];

export async function GET() {
  try {
    // 1. Fetch featured fragrances with origin brand
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
      WHERE d.canonical_name = ANY(${FEATURED_POPULAR_NAMES})
    `;

    // Map by dna_id and by canonical_name
    const dnaById = new Map(dnas.map((d: any) => [d.dna_id, d]));
    const dnaByName = new Map(dnas.map((d: any) => [d.canonical_name, d]));
    const sortedDnas = FEATURED_POPULAR_NAMES.map(name => dnaByName.get(name)).filter(Boolean);

    // 2. Fetch prices for each DNA
    const dnaIds = sortedDnas.map((d: any) => d.dna_id);
    
    if (dnaIds.length === 0) {
      return NextResponse.json([]);
    }

    const priceRows = await sql`
      SELECT 
        l.dna_id,
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
      WHERE l.dna_id = ANY(${dnaIds})
      ORDER BY p.price_amount ASC
    `;

    // Group price rows by dna_id and variant_id with strict matching
    const pricesByDna: Record<string, any[]> = {};
    for (const row of priceRows) {
      if (!row.source_url) continue;
      const dna = dnaById.get(row.dna_id);
      if (!dna) continue;

      const priceAmount = parseFloat(row.price_amount);
      const isMatch = isStrictMatch(
        row.source_url,
        row.source_url,
        priceAmount,
        dna.brand_name || '',
        dna.canonical_name || '',
        Boolean(dna.is_dupe),
        true
      );
      if (!isMatch) continue;

      let rName = row.retailer_name;
      if (!rName || rName === 'Unknown') {
        try {
          rName = new URL(row.source_url).hostname.replace('www.', '');
        } catch {
          rName = 'Retailer';
        }
      }

      const cleanUrl = cleanSourceUrl(row.source_url);
      if (!pricesByDna[row.dna_id]) {
        pricesByDna[row.dna_id] = [];
      }

      // Deduplicate by retailer name or URL
      const alreadyHas = pricesByDna[row.dna_id].some((p: any) => p.source_url === cleanUrl);
      if (alreadyHas) continue;

      pricesByDna[row.dna_id].push({
        price_observation_id: row.price_observation_id,
        retailer_name: rName,
        price_amount: priceAmount,
        currency_code: row.currency_code,
        source_url: cleanUrl,
        captured_at: row.captured_at,
        volume_ml: row.volume_ml ? parseFloat(row.volume_ml) : null,
        package_type: row.package_type
      });
    }

    const responses = sortedDnas.map((dna: any) => {
      const prices = pricesByDna[dna.dna_id] || [];
      return {
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
        clones: []
      };
    });

    return NextResponse.json(responses);
  } catch (error: any) {
    console.error('Error fetching trending fragrances:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
