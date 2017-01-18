CREATE TABLE fml ( 
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    fml_id   INTEGER,
    dt       TEXT,
    msg      TEXT
);

CREATE UNIQUE INDEX unique_id on fml(fml_id);

