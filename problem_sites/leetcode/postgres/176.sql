SELECT salary AS SecondHighestSalary
FROM (
    SELECT salary
    FROM Employee
    UNION ALL
    SELECT NULL AS salary
    UNION ALL
    SELECT NULL AS salary
) AS combined
LIMIT 1 OFFSET 1;
