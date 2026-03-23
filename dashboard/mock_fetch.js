import { createClient } from '@insforge/sdk';

const insforge = createClient({
  baseUrl: 'https://58izx8nr.us-east.insforge.app',
  anonKey: 'ik_162b8517243edf37df290152f6a0490f'
});

// Override global fetch
global.fetch = async (url, options) => {
  console.log("=== THE REAL URL IS: ===");
  console.log(url);
  console.log("=== HEADERS ARE: ===");
  console.log(options.headers);
  console.log("========================");
  return {
    ok: true,
    status: 200,
    headers: new Map(),
    json: async () => []
  };
};

async function test() {
  await insforge.database.from('moving_leads').select('*');
}

test().catch(console.error);
