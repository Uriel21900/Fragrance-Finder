import { neon } from '@neondatabase/serverless';

export const VERIFIED_NEON_URL = 
  "postgresql://neondb_owner:npg_iN45StWGXmpK@ep-winter-surf-ay718z8s-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require";

// If process.env.DATABASE_URL points to an older or unpurged database, ensure we use our verified Neon production cluster
const envUrl = process.env.DATABASE_URL;
const connectionString = (envUrl && envUrl.includes("ep-winter-surf-ay718z8s"))
  ? envUrl
  : VERIFIED_NEON_URL;

export const sql = neon(connectionString);
