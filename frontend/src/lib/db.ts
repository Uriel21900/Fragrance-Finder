import { neon } from '@neondatabase/serverless';

let client: ReturnType<typeof neon> | null = null;

function getClient(): ReturnType<typeof neon> {
  if (!client) {
    const url = process.env.DATABASE_URL;
    if (!url) {
      throw new Error(
        'DATABASE_URL environment variable is not defined. Please configure it in your environment.'
      );
    }
    client = neon(url);
  }
  return client;
}

// Lazy Proxy: Prevents early initialization failure during build-time page analysis
// and completely eliminates hardcoded/dummy connection strings from source code.
export const sql = new Proxy((() => {}) as unknown as ReturnType<typeof neon>, {
  apply(_target, thisArg, argArray) {
    return Reflect.apply(getClient(), thisArg, argArray);
  },
  get(_target, prop, receiver) {
    const c = getClient();
    const val = Reflect.get(c, prop, receiver);
    return typeof val === 'function' ? val.bind(c) : val;
  },
});

