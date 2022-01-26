BEGIN;

DROP TABLE IF EXISTS info;

CREATE TABLE info (
    id SERIAL PRIMARY KEY,
    data jsonb NOT NULL,
    comment TEXT
);

COMMIT;
