SELECT
    a.id AS author_id,
    a.name,
    a.birth_date,
    a.death_date,
    a.nationality,
    a.sex,
    a.bio,
    a.author_link,
    COALESCE(json_agg(DISTINCT b.title) FILTER (WHERE b.title IS NOT NULL), '[]') AS books
FROM authors a
LEFT JOIN book_authors ba ON a.id = ba.author_id
LEFT JOIN books b ON ba.book_id = b.id
GROUP BY a.id
ORDER BY a.name;
