import { NextResponse } from 'next/server';
import { sql } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { email, dna_id, target_price } = body;

    if (!email || !dna_id || !target_price) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
    }

    await sql`
      INSERT INTO fragrance_alert (email, dna_id, target_price)
      VALUES (${email}, ${dna_id}, ${target_price})
    `;

    return NextResponse.json({ message: 'Alert created successfully' });
  } catch (error: any) {
    console.error('Error creating alert:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
