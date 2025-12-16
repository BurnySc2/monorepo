SELECT
    firstName AS firstName,
    lastName AS lastName,
    city,
    state
FROM Person AS p
LEFT JOIN Address AS a ON p.personId = a.personId
