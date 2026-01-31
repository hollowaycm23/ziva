-- Adicionar peer spacex-2 (Ziva) na Gabrielle
INSERT OR REPLACE INTO peers (node_id, public_key, trust_level, last_seen) 
VALUES ('spacex-2', 'ziva-trust-key', 100, datetime('now'));

-- Verificar
SELECT * FROM peers;
