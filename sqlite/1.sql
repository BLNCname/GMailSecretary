CREATE TABLE IF NOT EXISTS users
(
    user_id TEXT PRIMARY KEY,
    telegram_id   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_tokens
(
    user_id TEXT PRIMARY KEY,
    token   TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);