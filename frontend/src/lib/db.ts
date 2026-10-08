import { neon } from '@neondatabase/serverless';

const connectionString = process.env.DATABASE_URL;

if (!connectionString) {
  console.warn('[db.ts] WARNING: DATABASE_URL environment variable is not defined.');
}

export const sql = neon(connectionString || '');
