import random

EMPTY = 0
FULL = 1

def create_grid(width, height):
    """ Create a grid with empty cells on odd row/column combinations. """
    grid = []
    for row in range(height):
        grid.append([])
        for column in range(width):
            if column % 2 == 1 and row % 2 == 1:
                grid[row].append(EMPTY)
            elif column == 0 or row == 0 or column == width - 1 or row == height - 1:
                grid[row].append(FULL)
            else:
                grid[row].append(FULL)
    return grid

#DFS maze
def create_maze(maze_width, maze_height):
    # Initialize the maze grid
    maze = create_grid(maze_width, maze_height)

    # Compute number of cells along width and height in the maze
    cells_wide = (maze_width - 1) // 2
    cells_high = (maze_height - 1) // 2

    # Create a grid to keep track of visited cells, with a border marked as visited
    # Create a 2D list to track visited cells
    visited = []
    for _ in range(cells_high):
        # Each row has 'cells_wide' number of False (not visited), and an extra True at the end (border)
        row = [False] * cells_wide + [True]
        visited.append(row)
    # Add an additional row at the bottom of the grid to mark it as visited (acts as a border)
    visited.append([True] * (cells_wide + 1))

    def walk(x, y):

        # Mark the current cell as visited
        visited[y][x] = True

        # Directions: left, down, right, up
        directions = [(x - 1, y), (x, y + 1), (x + 1, y), (x, y - 1)]
        random.shuffle(directions)  # Randomize directions to ensure maze variability

        for (next_x, next_y) in directions:
            if visited[next_y][next_x]:
                continue  # Skip already visited cells
            
            # Open a path between the current cell and the chosen adjacent cell
            # Check if the movement is vertical
            if next_x == x:
                # Calculate the row index for the path
                path_row = max(y, next_y) * 2
                # Calculate the column index for the path
                path_col = x * 2 + 1
                # Set the path cell to empty
                maze[path_row][path_col] = EMPTY
            # Check if the movement is horizontal
            elif next_y == y:
                # Calculate the row index for the path
                path_row = y * 2 + 1
                # Calculate the column index for the path
                path_col = max(x, next_x) * 2
                # Set the path cell to empty
                maze[path_row][path_col] = EMPTY

            
            # Recursively visit the next cell
            walk(next_x, next_y)

    # Start the maze generation from a random cell within the grid
    walk(random.randrange(cells_wide), random.randrange(cells_high))

    return maze