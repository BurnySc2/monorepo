WITH to_keep AS (
    SELECT min(id) AS id FROM Person
    GROUP BY email
),

to_delete AS (
    SELECT p1.id AS id FROM Person AS p1
    LEFT JOIN to_keep AS t ON p1.id = t.id
    WHERE t.id IS null
)

DELETE FROM Person
WHERE id IN (SELECT id FROM to_delete)
