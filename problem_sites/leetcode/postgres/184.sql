WITH highest_salary AS (
    SELECT
        departmentId,
        max(salary) AS salary
    FROM Employee
    GROUP BY departmentId
)

SELECT
    d.name AS Department,
    e.name AS Employee,
    e.salary AS Salary
FROM Employee AS e INNER JOIN Department AS d ON e.departmentId = d.id
INNER JOIN highest_salary AS h ON e.salary = h.salary AND d.id = h.departmentId
