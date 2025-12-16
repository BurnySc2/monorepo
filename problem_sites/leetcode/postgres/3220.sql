-- Write your PostgreSQL query statement below
SELECT
    t1.transaction_date,
    COALESCE(odd_sum, 0) AS odd_sum,
    COALESCE(even_sum, 0) AS even_sum
FROM (
    (
        SELECT transaction_date
        FROM transactions
        GROUP BY transaction_date
    ) AS t1
    LEFT JOIN
        (
            SELECT
                transaction_date,
                SUM(amount) AS even_sum
            FROM transactions
            WHERE MOD(amount, 2) = 0
            GROUP BY transaction_date
        ) AS t2
        ON t1.transaction_date = t2.transaction_date
    LEFT JOIN
        (
            SELECT
                transaction_date,
                SUM(amount) AS odd_sum
            FROM transactions
            WHERE MOD(amount, 2) = 1
            GROUP BY transaction_date
        ) AS t3
        ON t1.transaction_date = t3.transaction_date
)
ORDER BY t1.transaction_date ASC
