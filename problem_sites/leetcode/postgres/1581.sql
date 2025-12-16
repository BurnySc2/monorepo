-- Write your PostgreSQL query statement below
SELECT
    v1.customer_id,
    SUM(v2.count_no_trans) AS count_no_trans
FROM
(
    (
        SELECT customer_id
        FROM Visits
        WHERE visit_id NOT IN (SELECT visit_id FROM Transactions)
        GROUP BY customer_id
    ) AS v1
    LEFT JOIN
        (
            SELECT
                customer_id,
                visit_id,
                COUNT(customer_id) AS count_no_trans
            FROM Visits
            WHERE visit_id NOT IN (SELECT visit_id FROM Transactions)
            GROUP BY customer_id, visit_id, customer_id
        ) AS v2
        ON v1.customer_id = v2.customer_id
)
GROUP BY v1.customer_id, v2.count_no_trans
-- ORDER BY SUM(v2.count_no_trans) DESC, v1.customer_id ASC
