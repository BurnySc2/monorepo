class Solution:
    def numIslands(self, grid: list[list[str]]) -> int:
        color = 1
        new_grid = [[0 for _x in range(len(grid[0]))] for _y in range(len(grid))]

        def flood_fill(
            islands_grid: list[list[str]],
            color_grid: list[list[int]],
            index_y: int,
            index_x: int,
            my_color: int,
            already_checked_set: set[tuple[int, int]],
        ) -> None:
            # Check boundaries
            if index_y < 0 or len(islands_grid) <= index_y:
                # print(f"Returning because y is out of bounds: {index_y} {len(islands_grid)}")
                return
            if index_x < 0 or len(islands_grid[0]) <= index_x:
                # print(f"Returning because x is out of bounds: {index_x} {len(islands_grid[0])}")
                return
            already_checked_set.add((index_y, index_x))
            # Return early if current location has color
            if color_grid[index_y][index_x] != 0:
                return
            # Return early if current location is water
            if islands_grid[index_y][index_x] == "0":
                return

            color_grid[index_y][index_x] = my_color

            # Recursively floodfill neighboring "land"
            for offset in [
                (0, 1),
                (1, 0),
                (0, -1),
                (-1, 0),
            ]:
                new_y = index_y + offset[0]
                new_x = index_x + offset[1]
                if (new_y, new_x) in already_checked:
                    continue
                flood_fill(
                    islands_grid,
                    color_grid,
                    new_y,
                    new_x,
                    my_color,
                    already_checked_set,
                )

        for y, row in enumerate(grid):
            for x, _cell_value in enumerate(row):
                cell_value = grid[y][x]
                if cell_value == "1" and new_grid[y][x] == 0:
                    already_checked: set[tuple[int, int]] = set()
                    flood_fill(grid, new_grid, y, x, color, already_checked)
                    color += 1

        # Amount of colors used is the same as the amount of islands
        return color - 1


if __name__ == "__main__":
    s = Solution()

    grid1 = [
        ["1", "1", "1", "1", "0"],
        ["1", "1", "0", "1", "0"],
        ["1", "1", "0", "0", "0"],
        ["0", "0", "0", "0", "0"],
    ]
    expected1 = 1
    calculated1 = s.numIslands(grid1)
    assert expected1 == calculated1, (expected1, calculated1)

    grid2 = [
        ["1", "1", "0", "0", "0"],
        ["1", "1", "0", "0", "0"],
        ["0", "0", "1", "0", "0"],
        ["0", "0", "0", "1", "1"],
    ]
    expected2 = 3
    calculated2 = s.numIslands(grid2)
    assert expected2 == calculated2, (expected2, calculated2)
