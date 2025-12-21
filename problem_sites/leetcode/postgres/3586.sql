-- Not completed!
-- Does not work with 2 positive then a negative test, as it takes the difference between the later positive test to negative test
WITH recovered AS (
    SELECT
        c1.patient_id,
        c2.test_date - c1.test_date AS recovery_time

    FROM covid_tests AS c1
    INNER JOIN
        covid_tests AS c2
        ON
            c1.patient_id = c2.patient_id
            AND c1.test_date < c2.test_date
            AND c1.result = 'Positive'
            AND c2.result = 'Negative'
)

SELECT
    p.patient_id,
    p.patient_name,
    p.age,
    min(r.recovery_time) AS recovery_time
FROM patients AS p
INNER JOIN recovered AS r ON p.patient_id = r.patient_id
GROUP BY p.patient_id, p.patient_name, p.age
ORDER BY min(r.recovery_time) ASC, p.patient_name ASC
