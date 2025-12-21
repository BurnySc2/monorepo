SELECT DISTINCT l1.num AS ConsecutiveNums FROM Logs AS l1, Logs AS l2, Logs AS l3
WHERE
    l1.id + 1 = l2.id AND l1.id + 2 = l3.id
    AND l1.num = l2.num AND l1.num = l3.num
