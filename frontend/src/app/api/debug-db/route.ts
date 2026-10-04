import { NextResponse } from 'next/server';
import { sql } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const dbInfo = await sql`SELECT current_database(), inet_server_addr(), version();`;
    const envUrl = process.env.DATABASE_URL || 'NOT_SET';
    const masked = envUrl.replace(/:[^:@]+@/, ':***@');
    
    // Check aventus price count in whatever database this is
    const id = '9d5c1869-8bb3-48a3-9527-1e0563794520';
    const count = await sql`
      SELECT count(*)
      FROM fragrance_line l
      JOIN fragrance_product fp ON l.line_id = fp.line_id
      JOIN product_variant v ON fp.product_id = v.product_id
      JOIN price_observation p ON v.variant_id = p.variant_id
      WHERE l.dna_id = ${id}
    `;

    const samplePrices = await sql`
      SELECT p.price_amount, p.source_url
      FROM fragrance_line l
      JOIN fragrance_product fp ON l.line_id = fp.line_id
      JOIN product_variant v ON fp.product_id = v.product_id
      JOIN price_observation p ON v.variant_id = p.variant_id
      WHERE l.dna_id = ${id}
      LIMIT 10
    `;

    return NextResponse.json({
      buildTimestamp: new Date().toISOString(),
      commit: 'ae4b5dc-debug',
      maskedUrl: masked,
      dbInfo,
      aventusPriceCount: count[0]?.count,
      samplePrices
    });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
