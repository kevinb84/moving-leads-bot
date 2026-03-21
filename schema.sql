-- Create moving_leads table
CREATE TABLE IF NOT EXISTS moving_leads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    customer_name TEXT,
    phone_number TEXT,
    move_date TEXT,
    origin_neighborhood TEXT,
    destination_city TEXT,
    inventory_summary TEXT,
    packing_service BOOLEAN,
    call_summary TEXT,
    raw_text TEXT,
    source_url TEXT UNIQUE,
    text_hash TEXT UNIQUE,
    estimated_quote TEXT,
    whatsapp_draft TEXT,
    is_moving_lead BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS just to be safe, but allow public read/write for now to make it easy for our dashboard later.
ALTER TABLE moving_leads ENABLE ROW LEVEL SECURITY;

-- Allow anyone to read leads (useful for your Dashboard UI later)
CREATE POLICY "Enable read access for all users" ON "public"."moving_leads"
AS PERMISSIVE FOR SELECT
TO public
USING (true);

-- Allow REST API with service key to insert (it bypasses RLS anyway but this is good practice)
CREATE POLICY "Enable insert for authenticated users only" ON "public"."moving_leads"
AS PERMISSIVE FOR INSERT
TO authenticated
WITH CHECK (true);
