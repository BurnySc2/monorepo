-- https://www.codewars.com/kata/64956edc8673b3491ce5ad2c/train/sql
WITH failed_table AS (
  SELECT student_id, 'failed in ' || string_agg(format('%s(%s)', course_name, score), ', ') AS reason
  FROM (
    SELECT * FROM courses
    ORDER BY course_name ASC
  ) AS courses2
  WHERE score < 60
  GROUP BY student_id
  HAVING 3 <= count(*)
)

-- All student who 'quit studying':
SELECT id AS student_id, name, 'quit studying' AS reason FROM students
WHERE id NOT IN (SELECT student_id FROM courses)

UNION ALL

-- All student who 'failed too many courses':
SELECT id AS student_id, name, reason
FROM students s1
LEFT JOIN
failed_table
ON s1.id = failed_table.student_id
WHERE s1.id IN (SELECT student_id FROM failed_table)
ORDER BY student_id

