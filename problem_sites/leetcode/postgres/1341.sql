WITH most_rated_users AS (
    SELECT u.name AS results
    FROM Users AS u
    INNER JOIN MovieRating AS r ON u.user_id = r.user_id
    GROUP BY u.name
    ORDER BY count(*) DESC, u.name ASC
    LIMIT 1
),

highest_rated_movie AS (
    SELECT m.title AS results
    FROM Movies AS m
    INNER JOIN MovieRating AS r ON m.movie_id = r.movie_id
    WHERE r.created_at BETWEEN '2020-02-01' AND '2020-02-29'
    GROUP BY m.title
    ORDER BY avg(r.rating) DESC, m.title ASC
    LIMIT 1
)

SELECT results FROM most_rated_users
UNION ALL
SELECT results FROM highest_rated_movie
