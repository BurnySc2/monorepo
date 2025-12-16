SELECT email
FROM Person
GROUP BY email
HAVING 1 < count(*)
