import { neon } from '@neondatabase/serverless';

// Fallback to placeholder connection string during build-time page analysis if DATABASE_URL is not set
const connectionString = 
  process.env.DATABASE_URL || 
  'postgresql://placeholder_user:placeholder_pass@placeholder.neon.tech/neondb?sslmode=require';

export const sql = neon(connectionString);
