WITH all_ids AS (
    SELECT requester_id AS id FROM RequestAccepted
    UNION ALL
    SELECT accepter_id AS id FROM RequestAccepted
)

SELECT
    id,
    count(id) AS num
FROM all_ids
GROUP BY id
ORDER BY num DESC
LIMIT 1
