SELECT
    ae.author_id,
    a.name,
    ae.model_name,
    ae.vector
FROM author_embeddings ae
JOIN authors a ON ae.author_id = a.id
ORDER BY a.name;
