SELECT
    b.isbn,
    b.title,
    CAST(SUBSTRING(b.published_date, 1, 4) AS INTEGER) AS publishing_year,
    b.description,
    b.page_count,
    b.language,
    COALESCE(json_agg(DISTINCT a.name) FILTER (WHERE a.name IS NOT NULL), '[]') AS authors,
    COALESCE(json_agg(DISTINCT c.name) FILTER (WHERE c.name IS NOT NULL), '[]') AS categories
FROM books b
LEFT JOIN book_authors ba ON b.id = ba.book_id
LEFT JOIN authors a ON ba.author_id = a.id
LEFT JOIN book_categories bc ON b.id = bc.book_id
LEFT JOIN categories c ON bc.category_id = c.id
GROUP BY b.id
ORDER BY b.title;
