from typing import List


class Solution:
    def generateParenthesis(self, n: int) -> List[str]:
        listbro = [[], ["()"]]
        for i1 in range(2, n + 1):
            new_set = set()
            for j1 in listbro[i1 - 1]:
                new_set.add("(" + j1 + ")")
            for i2 in range(i1):
                i3 = i1 - i2
                if i3 > i2:
                    continue
                if i2 == 0 or i1 == 0:
                    continue
                for j1 in listbro[i2]:
                    for j2 in listbro[i3]:
                        new_set.add(j1 + j2)
                        if j2 + j1 != j1 + j2:
                            new_set.add(j2 + j1)
            listbro.append(sorted(new_set))
        return listbro[n]


app = Solution()
sol = app.generateParenthesis(4)
print()

from typing import List

#
# class Solution:
#     def generateParenthesis(self, n: int) -> List[str]:
#         listbro = [[], ["()"]]
#         for i1 in range(2, n+1):
#             new_set = set()
#             for i2 in range(i1):
#                 i3 = i1-i2
#                 if i2 == 0 or i1 == 0:
#                     continue
#                 for j1 in listbro[i2]:
#                     for j2 in listbro[i3]:
#                         new_set.add(j1+j2)
#                         new_set.add(j2+j1)
#                     if i2 == i1-1:
#                         new_set.add("("+j1+")")
#             listbro.append(sorted(new_set))
#         return listbro[n]
