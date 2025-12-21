WITH peak_hours AS (
    SELECT
        customer_id,
        count(*) AS count
    FROM restaurant_orders
    WHERE
        order_timestamp::time BETWEEN '11:00:00' AND '14:00:00'
        OR order_timestamp::time BETWEEN '18:00:00' AND '21:00:00'
    GROUP BY customer_id
),

rated AS (
    SELECT
        customer_id,
        count(*) AS count,
        avg(order_rating) AS average
    FROM restaurant_orders
    WHERE order_rating IS NOT null
    GROUP BY customer_id
)

SELECT
    r.customer_id,
    count(*) AS total_orders,
    round(100 * ph.count::decimal / count(*)) AS peak_hour_percentage,
    round(rated.average, 2) AS average_rating
FROM restaurant_orders AS r
INNER JOIN peak_hours AS ph ON r.customer_id = ph.customer_id
INNER JOIN rated ON ph.customer_id = rated.customer_id

GROUP BY r.customer_id, ph.count, rated.average, rated.count
HAVING
    3 <= count(*)
    AND 0.6 <= ph.count::decimal / count(*)
    AND 4.0 <= rated.average
    AND 0.5 <= rated.count::decimal / count(*)

ORDER BY average_rating DESC, customer_id DESC
