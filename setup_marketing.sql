CREATE TABLE IF NOT EXISTS marketing_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform TEXT NOT NULL,
    target_url TEXT,
    content TEXT NOT NULL,
    image_path TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT now()
);
GRANT ALL ON TABLE marketing_queue TO anon, authenticated, service_role;
NOTIFY pgrst, 'reload schema';
