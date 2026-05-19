SELECT
    be.book_id,
    b.title,
    be.model_name,
    be.vector
FROM book_embeddings be
JOIN books b ON be.book_id = b.id
ORDER BY b.title;
