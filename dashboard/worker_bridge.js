import { createClient } from '@insforge/sdk';

const insforge = createClient({
  baseUrl: 'https://58izx8nr.us-east.insforge.app',
  anonKey: 'ik_162b8517243edf37df290152f6a0490f' // Using the specific dashboard API key
});

export async function fetchJobs() {
  try {
    const { data, error } = await insforge.database
      .from('moving_leads')
      .select('*')
      .eq('customer_name', 'MARKETING_BROADCAST_PENDING')
      .limit(5);
      
    if (error) throw error;
    console.log(JSON.stringify(data || []));
  } catch (err) {
    console.log("[]");
  }
}

export async function markJobDone() {
  const args = process.argv.slice(2);
  const id = args[1];
  const status = args[2];
  if (!id || !status) return;
  
  await insforge.database
    .from('moving_leads')
    .update({ customer_name: status })
    .eq('id', id);
}

async function run() {
  const command = process.argv[2];
  if (command === 'fetch') {
    await fetchJobs();
  } else if (command === 'update') {
    await markJobDone();
  }
}

run();
