-- Optimized for high-throughput sequential chat writes
CREATE KEYSPACE IF NOT EXISTS llamaindex_store 
WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE TABLE IF NOT EXISTS llamaindex_store.chat_history (
    session_id text,
    message_id timeuuid,
    role text,
    content text,
    additional_kwargs text,
    PRIMARY KEY (session_id, message_id)
) WITH CLUSTERING ORDER BY (message_id ASC);
