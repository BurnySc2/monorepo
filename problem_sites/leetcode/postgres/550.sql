WITH distinct_player_id AS (SELECT DISTINCT player_id FROM Activity),

first_login_date AS (
    SELECT
        player_id,
        min(event_date) AS event_date
    FROM Activity
    GROUP BY player_id
),

matching AS (
    SELECT count(*) AS count
    FROM Activity AS a1
    INNER JOIN Activity AS a2 ON a1.player_id = a2.player_id
    INNER JOIN first_login_date AS f ON a1.player_id = f.player_id AND a1.event_date = f.event_date
    WHERE a1.event_date + 1 = a2.event_date
)

SELECT round(m.count::decimal / count(d), 2) AS fraction
FROM matching AS m
LEFT JOIN distinct_player_id ON true
GROUP BY m.count
