import socket
import threading
import time
import arcade
import random
import timeit
import os
import ast

NATIVE_SPRITE_SIZE = 165
SPRITE_SCALING = 0.28
SPRITE_SIZE = int(NATIVE_SPRITE_SIZE * SPRITE_SCALING)
game_started = False
countdown = 3
maze = None
game_won = False
portals = {}
#portals obj to store address of peeer , portal location, and whether it is active or not

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 300
SCREEN_TITLE = "Maze Depth First Example"

MOVEMENT_SPEED = 5

TILE_EMPTY = 0
TILE_CRATE = 1

# Maze must have an ODD number of rows and columns.
# Walls go on EVEN rows/columns.
# Openings go on ODD rows/columns
MAZE_HEIGHT = 21
MAZE_WIDTH = 21

MERGE_SPRITES = True

# How many pixels to keep as a minimum margin between the character
# and the edge of the screen.
VIEWPORT_MARGIN = 200


def create_grid(width, height):
    """ Create a grid with empty cells on odd row/column combinations. """
    grid = []
    for row in range(height):
        grid.append([])
        for column in range(width):
            if column % 2 == 1 and row % 2 == 1:
                grid[row].append(TILE_EMPTY)
            elif column == 0 or row == 0 or column == width - 1 or row == height - 1:
                grid[row].append(TILE_CRATE)
            else:
                grid[row].append(TILE_CRATE)
    return grid


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
                maze[path_row][path_col] = TILE_EMPTY
            # Check if the movement is horizontal
            elif next_y == y:
                # Calculate the row index for the path
                path_row = y * 2 + 1
                # Calculate the column index for the path
                path_col = max(x, next_x) * 2
                # Set the path cell to empty
                maze[path_row][path_col] = TILE_EMPTY

            
            # Recursively visit the next cell
            walk(next_x, next_y)

    # Start the maze generation from a random cell within the grid
    walk(random.randrange(cells_wide), random.randrange(cells_high))

    return maze


class MyGame(arcade.Window):
    """ Main application class. """
    #global array of players
    def __init__(self, width, height, title, maze, keep_track):
        """
        Initializer
        """
        super().__init__(width, height, title, resizable=True)

        # Set the working directory (where we expect to find files) to the same
        # directory this .py file is in. You can leave this out of your own
        # code, but it is needed to easily run the examples using "python -m"
        # as mentioned at the top of this program.
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        # Sprite lists
        self.wall_list = None

        # Player info
        self.score = 0
        self.player_sprite = None

        # Physics engine
        self.physics_engine = None

        # Used to scroll
        self.view_bottom = 0
        self.view_left = 0

        # Time to process
        self.processing_time = 0
        self.draw_time = 0

        self.countdown = 10
        self.start_time = time.time()

        self.last_row = None
        self.last_column = None

        self.drop_portal = False

        self.start_x = None
        self.start_y = None


    def setup(self):
        """ Set up the game and initialize the variables. """
        global maze, game_won, portals
        #print(maze)
        # Sprite lists
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.portal_list = arcade.SpriteList()
        self.enemy_portal_list = arcade.SpriteList()

        self.score = 0


        for row in range(MAZE_HEIGHT):
            for column in range(MAZE_WIDTH):
                if maze[row][column] == 1:
                    # Always initialize wall with a default to handle all cases.
                    wall = arcade.Sprite("./black_80x150.png", SPRITE_SCALING)

                    # Handle corners with specific sprite
                    if (row == 0 and column == 0) or (row == 0 and column == MAZE_WIDTH - 1) \
                    or (row == MAZE_HEIGHT - 1 and column == 0) or (row == MAZE_HEIGHT - 1 and column == MAZE_WIDTH - 1):
                        wall = arcade.Sprite("./80x80.png", SPRITE_SCALING)
                    elif column - 1 >= 0 and column + 1 < MAZE_WIDTH:
                        if maze[row][column+1] == 1 or maze[row][column-1] == 1:
                            if maze[row][column+1] == 1 and maze[row][column-1] == 1:
                                wall = arcade.Sprite("./black_150x80.png", SPRITE_SCALING)
                            else:
                                wall = arcade.Sprite("./80x80.png", SPRITE_SCALING)

                    wall.center_x = column * SPRITE_SIZE + SPRITE_SIZE / 2
                    wall.center_y = row * SPRITE_SIZE + SPRITE_SIZE / 2
                    self.wall_list.append(wall)

        # Set up the player
        self.player_sprite = arcade.Sprite("./zombie.png",
                                           SPRITE_SCALING + 0.1)
        self.player_list.append(self.player_sprite)
            

        # Randomly place the player. If we are in a wall, repeat until we aren't.
        placed = False
        while not placed:

            for row in reversed(range(MAZE_HEIGHT)):
              for column in reversed(range(MAZE_WIDTH)):
                if maze[row][column] == 0:
                    self.last_row = column * SPRITE_SIZE + SPRITE_SIZE / 2
                    self.last_column = row * SPRITE_SIZE + SPRITE_SIZE / 2
                    break

            # Randomly position
            for row in range(MAZE_HEIGHT):
              for column in range(MAZE_WIDTH):
                if maze[row][column] == 0:
                    self.player_sprite.center_x = column * SPRITE_SIZE + SPRITE_SIZE / 2
                    self.player_sprite.center_y = row * SPRITE_SIZE + SPRITE_SIZE / 2
                    self.start_x = column * SPRITE_SIZE + SPRITE_SIZE / 2
                    self.start_y = row * SPRITE_SIZE + SPRITE_SIZE / 2
                    #print( column * SPRITE_SIZE + SPRITE_SIZE / 2, row * SPRITE_SIZE + SPRITE_SIZE / 2)
                    placed = True
                    break

            # Are we in a wall?
            # walls_hit = arcade.check_for_collision_with_list(self.player_sprite, self.wall_list)
            # if len(walls_hit) == 0:
            #     # Not in a wall! Success!
            #     placed = True
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)
        #physics_engine = arcade.PhysicsEngineSimple(, self.wall_list)

        # Set the background color
        arcade.set_background_color(arcade.color.WHITE)

        # Set the viewport boundaries
        # These numbers set where we have 'scrolled' to.
        self.view_left = 0
        self.view_bottom = 0
        #print(f"Total wall blocks: {len(self.wall_list)}")

        print(f"{self.last_row}, {self.last_column}")
        threading.Thread(target=self.send_position_update, daemon=True).start()

    def on_draw(self):
        """
        Render the screen.
        """
        peer_texture = arcade.load_texture("./male_adv.png")
        global game_started, maze, game_won, portals
        # This command has to happen before we start drawing
        self.clear()

        # Start timing how long this takes
        draw_start_time = timeit.default_timer()
        
        self.wall_list.draw()
        self.player_list.draw()
        self.portal_list.draw()


        for pid, portal in portals.items():
            p = arcade.Sprite("./80x80.png", SPRITE_SCALING)
            #print(f"Creating portal at {portal[0]}, {portal[1]}")
            p.center_x = portal[0]
            p.center_y = portal[1]
            if(pid != own_address):
                self.enemy_portal_list.append(p)
            self.portal_list.append(p)

        portals_hit = arcade.check_for_collision_with_list(self.player_sprite, self.enemy_portal_list)
        if len(portals_hit)  > 0:
            print(f"Player teleported to {portals_hit[0].center_x}, {portals_hit[0].center_y}")
            self.player_sprite.center_x = self.start_x
            self.player_sprite.center_y = self.start_y#portals_hit[0].center_y
            for pid, portal in portals.items():
                if portal == (portals_hit[0].center_x, portals_hit[0].center_y):
                    portals[pid] = (0, 0)
                    portal_msg = f"portals {portals}"
                    send_message(sock, portal_msg)
            
       # print(portals)

        
        if(self.player_sprite.center_x >= self.last_row - 50 and self.player_sprite.center_x <= self.last_row + 50 and self.player_sprite.center_y >= self.last_column - 50 and self.player_sprite.center_y <= self.last_column + 50):
            game_won = True
            game_started = False
            send_message(sock, "game_won")
            arcade.draw_text("You win!", 100, 100, arcade.color.BLACK, 30)
            

        
        if not game_started:
            output = f"Game starting in {self.countdown} seconds"
            arcade.draw_text(output, 100, 1000, arcade.color.RED, 30)         


        for pid, position in peer_positions.items():
        
            if pid != own_address:  # Do not draw self
                #print(f"Drawing peer at {position}")
                
                if(position[0] >= self.last_row - 50 and position[0] <= self.last_row + 50 and position[1] >= self.last_column - 50 and position[1] <= self.last_column + 50):
                    game_won = True
                    game_started = False
                    print(f"{pid} Peer wins!")
                    arcade.draw_text("Peer wins!", 500, 500, arcade.color.WHITE, 16)
                if game_won:
                    game_started = False
                    print(f"{pid} Peer wins!")
                    arcade.draw_text("Peer wins!", 500, 500, arcade.color.WHITE, 16)
                    
                arcade.draw_circle_filled(position[0], position[1], SPRITE_SIZE / 3, arcade.color.BLUE)
                # Load the image for the sprite
                # peer_sprite = arcade.Sprite()
                # peer_sprite.texture = peer_texture
                # peer_sprite.scale = SPRITE_SCALING - 0.09
                # peer_sprite.set_position(position[0], position[1])
                
                # # Draw the peer sprite
                # peer_sprite.draw()

        if game_won:
            
            game_won = False
            if keep_track[own_address] == '2':
                #maze = create_maze(MAZE_WIDTH, MAZE_HEIGHT)
                send_maze(sock)
            self.start_time = time.time()
            self.setup()

                
        self.draw_time = timeit.default_timer() - draw_start_time

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """
        global portals
        if key == arcade.key.UP:
            self.player_sprite.change_y = MOVEMENT_SPEED
        elif key == arcade.key.DOWN:
            self.player_sprite.change_y = -MOVEMENT_SPEED
        elif key == arcade.key.LEFT:
            self.player_sprite.change_x = -MOVEMENT_SPEED
        elif key == arcade.key.RIGHT:
            self.player_sprite.change_x = MOVEMENT_SPEED
        
        if key == arcade.key.W:
            self.player_sprite.change_y = MOVEMENT_SPEED
        elif key == arcade.key.S:
            self.player_sprite.change_y = -MOVEMENT_SPEED
        elif key == arcade.key.A:
            self.player_sprite.change_x = -MOVEMENT_SPEED
        elif key == arcade.key.D:
            self.player_sprite.change_x = MOVEMENT_SPEED

        if key == arcade.key.ESCAPE:
            os._exit(0)
        
        if key == arcade.key.SPACE and self.drop_portal == False:
            self.drop_portal = True
            portals[own_address] = ((self.player_sprite.center_x, self.player_sprite.center_y))
        
            

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.UP or key == arcade.key.DOWN:
            self.player_sprite.change_y = 0
        elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player_sprite.change_x = 0
        elif key == arcade.key.W or key == arcade.key.S:
            self.player_sprite.change_y = 0
        elif key == arcade.key.A or key == arcade.key.D:
            self.player_sprite.change_x = 0

    def send_position_update(self):
        global portals
        while True:
            if self.player_sprite:
                portals_msg = f"portals {portals}"
                pos_msg = f"pos_update {own_address[0]}:{own_address[1]} {self.player_sprite.center_x} {self.player_sprite.center_y}"
                send_message(sock, pos_msg)
                send_message(sock, portals_msg)
            time.sleep(0.1)  # Update position every 100 ms
                
    def on_update(self, delta_time):
        """ Movement and game logic """
        start_time = timeit.default_timer()

        # Call update on all sprites (The sprites don't do much in this
        # example though.)
        #call initial timer to start game
        #TypeError: __main__.MyGame.initial_timer() argument after * must be an iterable, not MyGame
        global game_started
        #print( game_started)
        if(keep_track[own_address] == '2'):
            if not game_started:
                #print("ZAZA")
                
                elapsed_time = time.time() - self.start_time #time elapsed since game started
                self.countdown = max(0, 5 - int(elapsed_time)) #countdown from 10 to 0
                #print(self.countdown)
                send_message(sock, f"countdown {self.countdown}")
                if self.countdown == 0:
                    self.countdown = 5
                    game_started = True
                    print("Game started!")  # Debug messag


        if game_started:
            send_message(sock, "game_started")
            self.physics_engine.update()
        
        
        self.countdown = countdown
        #print(self.countdown)
        # --- Manage Scrolling ---

        # Track if we need to change the viewport

        changed = False

        # Scroll left
        left_bndry = self.view_left + VIEWPORT_MARGIN
        if self.player_sprite.left < left_bndry:
            self.view_left -= left_bndry - self.player_sprite.left
            changed = True

        # Scroll right
        right_bndry = self.view_left + SCREEN_WIDTH - VIEWPORT_MARGIN
        if self.player_sprite.right > right_bndry:
            self.view_left += self.player_sprite.right - right_bndry
            changed = True

        # Scroll up
        top_bndry = self.view_bottom + SCREEN_HEIGHT - VIEWPORT_MARGIN
        if self.player_sprite.top > top_bndry:
            self.view_bottom += self.player_sprite.top - top_bndry
            changed = True

        # Scroll down
        bottom_bndry = self.view_bottom + VIEWPORT_MARGIN
        if self.player_sprite.bottom < bottom_bndry:
            self.view_bottom -= bottom_bndry - self.player_sprite.bottom
            changed = True

        if changed:
            arcade.set_viewport(self.view_left,
                                SCREEN_WIDTH + self.view_left,
                                self.view_bottom,
                                SCREEN_HEIGHT + self.view_bottom)

        # Save the time it took to do this.
        self.processing_time = timeit.default_timer() - start_time
     
def send_maze(sock):
    for peer in keep_track:
        if(keep_track[own_address] == '2' and peer != own_address):
            #print(f"Creating maze: {maze}")
            message = f"maze {maze}"
            sock.sendto(message.encode('utf-8'), peer)
            #print(f"Sending {maze} to {peer}")


def get_host_ip():
    """Automatically determine the local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        IP = s.getsockname()[0]
        s.close()
    except Exception:
        IP = '127.0.0.1'
    return IP

def receive_messages(sock):
    global recv_maze, peer_positions, game_started, countdown, maze, game_won, portals
    peer_positions = {}
    while True:
        data, addr = sock.recvfrom(2048)
        message = data.decode('utf-8')
        #print(f"Received message from {addr}: {message}")
        if message.startswith("maze"):
            #strip message to "maze " and the rest 
            recv_maze = message[5:]
            #print(f"Received maze from {addr}: {recv_maze}")
            maze = eval(recv_maze)
            print(f"Received maze from {addr}: {recv_maze}")
        if message.startswith("countdown"):
            _, count = message.split()
            #print(f"Countdown: {count}")
            countdown = int(count)
        if message.startswith("game_started"):
            game_started = True
        if message.startswith("status"):
            _, ip, port, status = message.split()
            peer = (ip, int(port))
            keep_track[peer] = status
            #print(f"Status update from {peer}: {status}   pllllll")
        if message.startswith("pos_update"):
            #print(f"posupdate {message}")
            _, pid, x, y = message.split()
            ip, port = pid.split(':')
            peer_positions[pid] = (float(x), float(y))
        if message == "game_won":
            if keep_track[own_address] == '2':  # If host
                maze = create_maze(MAZE_WIDTH, MAZE_HEIGHT)  # Regenerate maze
                send_maze(sock)  # Send new maze to all
            game_won = True
            game_started = False
        if message.startswith("portals"):
            #print(f"Received portals: {message}")
            _, portal_data = message.split(' ', 1)
            #print(portal_data)
            portals_dict = ast.literal_eval(portal_data)
            for pid, position in portals_dict.items():
                # print(f"Player ID: {pid}")
                # print(f"Position: {position}")
                portals[pid] = position
                #print(f"Portals: {portals}")
         
        if addr not in peers:
            peers.append(addr)
            keep_track[addr] = '1'
            print(f"New peer added: {addr}")
            send_maze(sock)
        if(len(peers) == 1):
            keep_track[addr] = '2'
            #print(f"Updated host to {addr}")

        last_seen[addr] = time.time()

def send_message(sock, message):
    if(message.startswith("countdown") or message.startswith("game_won") or message.startswith("portals")):
        sock.sendto(message.encode('utf-8'), own_address)
    for peer in peers:
        if(peer != own_address):
            #print(f"Sending message to {peer}: {message}"
            sock.sendto(message.encode('utf-8'), peer)
    

def send_status(sock):
    for peer in peers:
        for p in keep_track:
            if(peer != own_address and p != peer):
                message = f"status {peer[0]} {peer[1]} {keep_track[peer]}"
                #print(f"Sending status update to {peer}: {keep_track[peer]}")
                sock.sendto(message.encode('utf-8'), p)
            elif(keep_track[peer] == '2'):
                message = f"status {peer[0]} {peer[1]} {keep_track[peer]}"
                #print(f"Sending status update to {peer}: {keep_track[peer]}")
                sock.sendto(message.encode('utf-8'), p)

def announce_presence(sock, own_port):
    message = f"hello from {own_port}"
    broadcast_address = '192.168.0.101'  # Ensure this is the correct broadcast address for your network
    sock.sendto(message.encode('utf-8'), (broadcast_address, 6969))

def heartbeat(sock, own_port):
    while True:
        time.sleep(5)
        send_message(sock, f"heartbeat from {own_port}")
        check_peers()

def check_peers():
    current_time = time.time()
    timeout = 7
    peers_to_remove = []

    for peer in peers:
        if current_time - last_seen.get(peer, 0) > timeout:
            peers_to_remove.append(peer)
            keep_track[peer] = '0'
            if peer in last_seen:
                del last_seen[peer]
            print(f"Peer {peer} has timed out and been removed.")

    # Remove peers outside the loop to prevent modification during iteration issues
    for peer in peers_to_remove:
        peers.remove(peer)

    # Update host after cleaning up timed-out peers
    update_host_peer()


def handle_user_input(sock):
    while True:
        command = input("Enter command (send <message>, list, check): ")
        if command.startswith("send "):
            message = command[5:]
            send_message(sock, message)
        elif command == "list":
            print("Connected peers:")
            for peer in peers:
                print(f"Peer: {peer}")
        elif command.startswith("check"):
            for p, status in keep_track.items():
                print(f"Peer: {p}, Status: {status}")

def update_host_peer():
    global keep_track, peers
    # Determine if a host already exists
    current_host = []
    for peer, status in keep_track.items():
        if status == '2':
            current_host.append(peer)

    if current_host:
        return  # If there's already a host, no need to update

    if not peers:
        print("No peers left to assign host.")
        return

    # Find the smallest address from the list of peers
    smallest_peer = min(peers, key=lambda x: (x[0], x[1]))
    keep_track[smallest_peer] = '2'
    print(f"Updated host to {smallest_peer}")

def update():
    while True:
        time.sleep(5)
        update_host_peer()
        send_status(sock)

def main():
    host = get_host_ip()
    port = int(input("Enter your port number: "))

    #broadcast_address = input("Enter the adress you want to connect to (Type 0 if none): ")
    #broadcast_port = input("Enter the port you want to connect to (Type 0 if none): ")

    global peers, last_seen, keep_track, own_address, sock, maze, recv_maze
    own_address = (host,port)
    keep_track = {(host, port): '1'}
    peers = [(host, port)]
    last_seen = {(host, port): time.time()}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind((host, port))

    announce_presence(sock, port)
    


    threading.Thread(target=receive_messages, args=(sock,)).start()
    threading.Thread(target=update, args=()).start()
    threading.Thread(target=handle_user_input, args=(sock,)).start()
    threading.Thread(target=heartbeat, args=(sock, port)).start()

    time.sleep(1)

    if(keep_track[own_address] == '2'):
        maze = create_maze(MAZE_WIDTH, MAZE_HEIGHT)
    else:
        #convert string to list
        maze = eval(recv_maze) 

    window = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, maze, keep_track)
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()