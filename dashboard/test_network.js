import { createClient } from '@insforge/sdk';

const insforge = createClient({
  baseUrl: 'https://58izx8nr.us-east.insforge.app',
  anonKey: 'ik_162b8517243edf37df290152f6a0490f'
});

async function test() {
  const { data, error } = await insforge.database.from('moving_leads').select('*');
  console.log("Error:", error);
  console.log("Data length:", data ? data.length : 0);
}

test().catch(console.error);
