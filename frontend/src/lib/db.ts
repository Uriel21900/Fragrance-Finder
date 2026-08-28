import { neon } from '@neondatabase/serverless';

const connectionString = process.env.DATABASE_URL || 
  "postgresql://neondb_owner:npg_iN45StWGXmpK@ep-winter-surf-ay718z8s-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require";

export const sql = neon(connectionString);
