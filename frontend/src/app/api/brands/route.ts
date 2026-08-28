import { NextResponse } from 'next/server';
import { sql } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const brands = await sql`
      SELECT name 
      FROM brand 
      ORDER BY name ASC
    `;
    return NextResponse.json(brands);
  } catch (error: any) {
    console.error('Error fetching brands:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
