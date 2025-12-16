SELECT d2.id FROM Weather AS d1
INNER JOIN Weather AS d2 ON d1.recordDate + 1 = d2.recordDate
WHERE d1.temperature < d2.temperature
