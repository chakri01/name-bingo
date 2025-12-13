CREATE TABLE IF NOT EXISTS names (
  id SERIAL PRIMARY KEY,
  name_text VARCHAR(100) UNIQUE NOT NULL,
  is_picked BOOLEAN DEFAULT false,
  picked_at TIMESTAMP,
  pick_order INTEGER
);

CREATE TABLE IF NOT EXISTS tickets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  grid JSONB NOT NULL,
  player_name VARCHAR(100),
  is_assigned BOOLEAN DEFAULT false,
  status VARCHAR(20) DEFAULT 'active',
  claimed_at TIMESTAMP,
  assigned_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS game_state (
  key VARCHAR(50) PRIMARY KEY,
  value JSONB NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS claim_queue (
  id SERIAL PRIMARY KEY,
  ticket_id UUID REFERENCES tickets(id),
  claimed_at TIMESTAMP DEFAULT NOW(),
  status VARCHAR(20) DEFAULT 'pending',
  verified_by VARCHAR(50),
  verified_at TIMESTAMP
);

CREATE INDEX idx_names_picked ON names(is_picked, pick_order);
CREATE INDEX idx_tickets_assigned ON tickets(is_assigned);
CREATE INDEX idx_claims_pending ON claim_queue(status, claimed_at);

INSERT INTO game_state (key, value) VALUES 
  ('game_started', 'false'),
  ('claim_lock', 'false')
ON CONFLICT (key) DO NOTHING;