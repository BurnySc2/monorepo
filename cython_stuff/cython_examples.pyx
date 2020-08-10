# distutils: language=c++
# cython: language_level=3

from cpython cimport array
import array

# Import https://en.cppreference.com/w/cpp/container/map
# See what is available: https://github.com/cython/cython/tree/master/Cython/Includes/libcpp python3.7/site-packages/Cython/Includes/libcpp
from libcpp.vector cimport vector as cpp_vector
from libcpp.map cimport map as cpp_map
from libcpp.unordered_map cimport unordered_map as cpp_unordered_map
from libcpp.set cimport set as cpp_set

from libcpp.deque cimport deque as cpp_deque
from libcpp.queue cimport queue as cpp_queue, priority_queue as cpp_priority_queue
from libcpp.stack cimport stack as cpp_stack

"""
TODO Write example for:
    int - uint, int64?
    float - double
    string - does it work?
    tuple - ?
    list - vector
    set - set
    dict - map
    numpy array - ?
manipulation
"""


def two_sum(list nums, int target):
    """
    Given an array of integers, return indices of the two numbers such that they add up to a specific target.

    You may assume that each input would have exactly one solution, and you may not use the same element twice.

    Example:
        Given nums = [2, 7, 11, 15], target = 9,

        Because nums[0] + nums[1] = 2 + 7 = 9,
        return [0, 1].
    """
    cdef:
        cpp_map[int, int] my_dict
        int val, value, index
    for index, value in enumerate(nums):
        val = target - value
        if my_dict.count(val) > 0:
            return [my_dict[val], index]
        my_dict[value] = index


def two_sum_vector(cpp_vector[int] nums, int target):
    cdef:
        cpp_map[int, int] my_dict
        int val, value, index
    for index, value in enumerate(nums):
        val = target - value
        if my_dict.count(val) > 0:
            return [my_dict[val], index]
        my_dict[value] = index


def primes(int nb_primes):
    """ Find the first X amount of primes"""
    cdef:
        int n, i, len_p
        int[10000] p
    if nb_primes > 10000:
        nb_primes = 10000
    len_p = 1  # The current number of elements in p
    p[0] = 2
    n = 3
    while len_p < nb_primes:
        # Is n prime?
        for i in p[:len_p]:
            if n % i == 0:
                break
        # If no break occurred in the loop, we have a prime
        else:
            p[len_p] = n
            len_p += 1
        n += 2
    # Let's return the result in a python list
    return [i for i in p[:len_p]]


def primes_vector(unsigned int nb_primes):
    cdef:
        int n, i
        cpp_vector[int] p
    # p.reserve(nb_primes)
    p.push_back(2)
    n = 3
    while p.size() < nb_primes:
        for i in p:
            if n % i == 0:
                break
        else:
            p.push_back(n)
        n += 2
    return p


# import numpy as np
# cimport numpy as np
# /home/burny/.local/share/virtualenvs/python-template-i7NJz989/lib/python3.7/site-packages/numpy/core/include

ctypedef cpp_vector[int] point
ctypedef cpp_map[point, point] my_map
cdef int in_bounds(int y, int x, int height, int width):
    if 0 <= y < height and 0 <= x < width:
        return 1
    return 0

cdef int is_wall(long[:, :] grid, int y, int x):
    if grid[y, x] == 0:
        return 1
    return 0

def test_map(cpp_map[point, point] came_from, point p):
    came_from[[1, 2]] = [3, 4]
    return came_from[p]

cdef cpp_vector[point] generate_path(my_map came_from, point start, point goal):
    cdef cpp_vector[point] path
    while start != goal:
        path.push_back(goal)
        goal = came_from[goal]
    return path

cdef cppclass MyNode:
    float distance
    point current
    point previous
    # 'Less than' trait https://stackoverflow.com/questions/22537683/how-to-make-a-c-mapping-from-c-struct-to-int-in-cython
    bint lessthan "operator<"(const MyNode t) const:
         return this.distance > t.distance

# Constructor of 'MyNode'
# cdef MyNode make_node(float distance, point current, point previous) nogil:
#     cdef MyNode node
#     node.distance = distance
#     node.current = current
#     node.previous = previous
#     return node

def dijkstra(long[:, :] grid, point start, point goal, diagonal=False):
    cdef:
        cpp_vector[point] path
        double distance
        my_map came_from
        cpp_priority_queue[MyNode] open_set
        double[8] distances
        # cpp_vector[float] distances
        cpp_vector[point] neighbors
        # int[8] neighbors_y, neighbors_x
        point new_point, current_point, previous_point
        MyNode node, new_node
        int neighbors_amount
    if start == goal:
        return 0, path
    node.distance = 0
    node.current = start
    node.previous = start
    open_set.push(node)
    sqrt2 = 2 ** 0.5
    distances = [1, 1, 1, 1, sqrt2, sqrt2, sqrt2, sqrt2]
    neighbors = [(-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    # neighbors_y = [-1, 0, 1, 0, -1, -1, 1, 1]
    # neighbors_x = [0, -1, 0, 1, -1, 1, -1, 1]
    if diagonal:
        neighbors_amount = 8
    else:
        neighbors_amount = 4
    height = grid.shape[0]
    width = grid.shape[1]

    while not open_set.empty():
        node = open_set.top()
        open_set.pop()
        if came_from.count(node.current) > 0:
            continue
        # distance_dict[node.current] = node.distance
        came_from[node.current] = node.previous

        # Generate Path if goal has been reached
        if came_from.count(goal) > 0:
            return node.distance, generate_path(came_from, start, goal)[::-1]

        for i in range(neighbors_amount):
            node_dist = distances[i]
            neighbor = neighbors[i]
            # neighbor_y = neighbors_y[i]
            # neighbor_x = neighbors_x[i]
            new_point = node.current[0] + neighbor[0], node.current[1] + neighbor[1]
            # new_point = node.current[0] + neighbor_y, node.current[1] + neighbor_x
            if in_bounds(new_point[0], new_point[1], height, width) == 0:
                continue
            if is_wall(grid, new_point[0], new_point[1]) == 1:
                continue
            if came_from.count(new_point) > 0:
                continue
            new_distance = node.distance + node_dist
            # new_node = make_node(new_distance, new_point, node.current)
            new_node.distance = new_distance
            new_node.current = new_point
            new_node.previous = node.current
            open_set.push(new_node)

    return -1, path
