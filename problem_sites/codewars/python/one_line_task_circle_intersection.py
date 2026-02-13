# TODO Unsolved!
# https://www.codewars.com/kata/5908242330e4f567e90000a3/train/python
circleIntersection=lambda a,b,r: 1.2284*max(0, ((2*r)-((b[1]-a[1])**2+(b[0]-a[0])**2)**0.5))**2

import math
def circleIntersection(a,b,r):
    const = (1/6) * (4 * math.pi - 3**1.5)
    # const = 1.2284
    r2 = 2*r
    dx = (b[1] - a[1])**2
    dy = (b[0] - a[0])**2
    width = r2 - (dx + dy)**0.5
    return const * max(0, width)**2

# a**2 + b**2 == c**2
# (b.x - a.x)**2 + (b.y - a.y)**2 == c**2

# 2*r - ( (b.x - a.x)**2 + (b.y - a.y)**2 )**0.5
# 2r - (dx - dy)**0.5
# 4r**2 - dx - dy
