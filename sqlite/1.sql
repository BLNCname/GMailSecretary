CREATE TABLE IF NOT EXISTS auth_tokens
(
    user_id TEXT PRIMARY KEY,
    token   TEXT NOT NULL
);