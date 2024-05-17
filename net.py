import socket
import threading
import time
import arcade
import random
import timeit
import os
from maze_generation import create_maze

""" Object size and scale """
INIT_OBJ_SIZE = 165
OBJ_SCALE = 0.28
OBJ_SIZE = int(INIT_OBJ_SIZE * OBJ_SCALE)

""" Screen size and title """
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
SCREEN_TITLE = "MazeN (Amazing) Game"

# min pixels from player to edge of the screen
VIEWPORT_MARGIN = 200

MOVEMENT_SPEED = 5

""" Maze constants """
# walls are odd, empty space is even
MAZE_HEIGHT = 21 # Must be an odd number
MAZE_WIDTH = 21 # Must be an odd number

""" Global variables """
game_started = False
game_won = False

countdown = 3
maze = None

portal_locations = {}
teleport_x = 0
teleport_y = 0
class MazeN(arcade.Window):
    
    def __init__(self, width, height, title, maze, keep_track):
        # Call the parent class's init function
        super().__init__(width, height, title, resizable=True) 

        self.wall_list = None
        self.player_object = None
        self.physics_engine = None # Used for collision detection

        self.dropped_portal = False

        self.closeby = False # Used to check if player is close to a portal
        self.closeby_x = 0
        self.closeby_y = 0

        # Used to scroll
        self.view_bottom = 0
        self.view_left = 0

        # Time to process
        self.processing_time = 0
        self.draw_time = 0

        self.countdown = 10 # Countdown before game starts
        self.start_time = time.time()

        self.end_x = None # End point
        self.end_y = None

        self.enemy_list = arcade.SpriteList()
        self.start_x = None # Start point
        self.start_y = None

    """ Set up the game """
    def setup(self):
        global maze, game_won
       
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()

        """ Set up the walls with images acting as objects """
        for row in range(MAZE_HEIGHT):
            for column in range(MAZE_WIDTH):
                if maze[row][column] == 1: # If it's a wall
                    
                    wall = arcade.Sprite("./assets/black_80x150.png", OBJ_SCALE) # Load default wall image for vertical walls
                    # Check if it's a corner wall
                    if (row == 0 and column == 0) or (row == 0 and column == MAZE_WIDTH - 1) \
                    or (row == MAZE_HEIGHT - 1 and column == 0) or (row == MAZE_HEIGHT - 1 and column == MAZE_WIDTH - 1):
                        
                        wall = arcade.Sprite("./assets/80x80.png", OBJ_SCALE) # Load corner wall image

                    elif column - 1 >= 0 and column + 1 < MAZE_WIDTH: # Check if it's a horizontal wall

                        if maze[row][column+1] == 1 or maze[row][column-1] == 1: # Check if there's a wall on either side

                            if maze[row][column+1] == 1 and maze[row][column-1] == 1: # Check if there's a wall on both sides
                                wall = arcade.Sprite("./assets/black_150x80.png", OBJ_SCALE) # Load horizontal wall image
                            else:
                                wall = arcade.Sprite("./assets/80x80.png", OBJ_SCALE) # Load corner wall image

                    # Set the wall's position
                    wall.center_x = column * OBJ_SIZE + OBJ_SIZE / 2
                    wall.center_y = row * OBJ_SIZE + OBJ_SIZE / 2
                    self.wall_list.append(wall)

        # Set up the player
        self.player_object = arcade.Sprite("./assets/zombie.png", OBJ_SCALE + 0.1)
        self.player_list.append(self.player_object)
            
        # Place the player
        placed = False
        while not placed:
            # get end point
            for row in reversed(range(MAZE_HEIGHT)):
              for column in reversed(range(MAZE_WIDTH)):
                if maze[row][column] == 0:
                    self.end_x = column * OBJ_SIZE + OBJ_SIZE / 2
                    self.end_y = row * OBJ_SIZE + OBJ_SIZE / 2
                    break

            # get start point and place player at start point
            for row in range(MAZE_HEIGHT):
              for column in range(MAZE_WIDTH):
                if maze[row][column] == 0:
                    self.player_object.center_x = column * OBJ_SIZE + OBJ_SIZE / 2
                    self.player_object.center_y = row * OBJ_SIZE + OBJ_SIZE / 2

                    self.start_x = column * OBJ_SIZE + OBJ_SIZE / 2
                    self.start_y = row * OBJ_SIZE + OBJ_SIZE / 2

                    placed = True
                    break

        # Create the physics engine for the player and walls
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_object, self.wall_list)
    
        # Set the background color
        arcade.set_background_color(arcade.color.WHITE)

        # Set the viewport boundaries
        # These numbers set where we have 'scrolled' to.
        self.left_view = 0
        self.bot_view = 0

        threading.Thread(target=self.send_position_update, daemon=True).start()

    def on_draw(self):

        global game_started, maze, game_won, portal_locations, teleport_x, teleport_y

        peer_texture = arcade.load_texture("./assets/male_adv.png")
        self.enemy_list = arcade.SpriteList()

        # This command has to happen before we start drawing
        self.clear()
        
        # Draw all the objects.
        self.wall_list.draw()
        self.player_list.draw()

        """ Draw the portals """
        for pid, portal in portal_locations.items(): # pid == peer id, portal == (x, y)
            if portal[0] != -1 and portal[1] != -1: # If the portal still exists
                
                prt = arcade.Sprite("./assets/50x50_beige.png", OBJ_SCALE)
                prt.center_x = portal[0]
                prt.center_y = portal[1]
                prt.draw()

                if portal[0] == -2 and portal[1] == -2 and pid == own_address: # If the portal has been destroyed
                    # teleport player who placed the portal to portal location
                    portal_locations[pid] = (-1, -1)
                    self.player_object.center_x = teleport_x
                    self.player_object.center_y = teleport_y

                if pid != own_address: # If the portal belongs to a peer

                    self.enemy_list.append(prt)  # Add the portal to the enemy list
                    if self.player_object.center_x >= portal[0] - 50 and self.player_object.center_x <= portal[0] + 50 and self.player_object.center_y >= portal[1] - 50 and self.player_object.center_y <= portal[1] + 50: # If the player is close to a portal
                        # save the portal's location
                        self.closeby = True
                        self.closeby_x = portal[0] 
                        self.closeby_y = portal[1]

        """ If a player has reached the end point """
        if(self.player_object.center_x >= self.end_x - 50 and self.player_object.center_x <= self.end_x + 50 and self.player_object.center_y >= self.end_y - 50 and self.player_object.center_y <= self.end_y + 50):

            game_won = True
            game_started = False
            send_message(sock, "game_won")
            arcade.draw_text("You win!", 100, 100, arcade.color.BLACK, 30)
            
        # Draw the countdown
        if not game_started:
            output = f"Game starting in {self.countdown} seconds"
            arcade.draw_text(output, 100, 1000, arcade.color.RED, 30)         

        """ Draw the peers with their real-time positions"""
        for pid, position in peer_positions.items():
            if pid != own_address:  
                # Check if the peer has reached the end point
                if(position[0] >= self.end_x - 50 and position[0] <= self.end_x + 50 and position[1] >= self.end_y - 50 and position[1] <= self.end_y + 50):
                    game_won = True
                    game_started = False
                    print(f"{pid} Peer wins!")
                    arcade.draw_text("Peer wins!", 500, 500, arcade.color.WHITE, 16)

                #arcade.draw_circle_filled(position[0], position[1], OBJ_SIZE / 3, arcade.color.BLUE)

                # Load the image for the sprite
                peer_sprite = arcade.Sprite()
                peer_sprite.texture = peer_texture
                peer_sprite.scale = OBJ_SCALE - 0.09
                peer_sprite.set_position(position[0], position[1])
                peer_sprite.draw()

        # Check if the game has been won
        if game_won:
            for pid, portal in portal_locations.items():
                if portal[0] != -1 and portal[1] != -1:
                    portal_locations[pid] = (-1, -1)
                    msg = f"portal {pid[0]} {pid[1]} {-1} {-1}"
                    send_message(sock, msg)
            self.dropped_portal = False
            game_won = False 
            # Regenerate the maze if player is host
            if keep_track[own_address] == '2': 
                send_maze(sock) # Send the new maze to all peers
            self.start_time = time.time()
            self.setup()
 

    def on_key_press(self, key, modifiers):
        """Called if a key is pressed. """
        global teleport_x, teleport_y
        if key == arcade.key.UP:
            self.player_object.change_y = MOVEMENT_SPEED
        elif key == arcade.key.DOWN:
            self.player_object.change_y = -MOVEMENT_SPEED
        elif key == arcade.key.LEFT:
            self.player_object.change_x = -MOVEMENT_SPEED
        elif key == arcade.key.RIGHT:
            self.player_object.change_x = MOVEMENT_SPEED
        elif key == arcade.key.W:
            self.player_object.change_y = MOVEMENT_SPEED
        elif key == arcade.key.S:
            self.player_object.change_y = -MOVEMENT_SPEED
        elif key == arcade.key.A:
            self.player_object.change_x = -MOVEMENT_SPEED
        elif key == arcade.key.D:
            self.player_object.change_x = MOVEMENT_SPEED
        elif key == arcade.key.ESCAPE:
            arcade.close_window()
        elif key == arcade.key.SPACE and self.dropped_portal == False:
            # Drop a portal on own location if one hasn't been dropped
            self.dropped_portal = True
            portal_locations[own_address] = (self.player_object.center_x, self.player_object.center_y)
            msg = f"portal {own_address[0]} {own_address[1]} {self.player_object.center_x} {self.player_object.center_y}"
            send_message(sock, msg)
        elif key == arcade.key.X and self.closeby:
            # If close to a portal and pressed X
            for pid, portal in portal_locations.items():
                # check which portal is close to player
                if self.closeby_x == portal[0] and self.closeby_y == portal[1]:
                    # save the portal's location
                    teleport_x = portal[0]
                    teleport_y = portal[1]    

                    msg = f"teleport {teleport_x} {teleport_y}"
                    send_message(sock, msg)

                    # -2, -2 means the portal has been destroyed       
                    portal_locations[pid] = (-2, -2)
                    msg = f"portal {pid[0]} {pid[1]} {-2} {-2}"
                    send_message(sock, msg) 

        

    def on_key_release(self, key, modifiers):
        """Called if user releases a key. """
        if key == arcade.key.UP or key == arcade.key.DOWN:
            self.player_object.change_y = 0
        elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player_object.change_x = 0
        elif key == arcade.key.W or key == arcade.key.S:
            self.player_object.change_y = 0
        elif key == arcade.key.A or key == arcade.key.D:
            self.player_object.change_x = 0

    def send_position_update(self):
        """Send the player's position and portals to all peers every 100 ms"""
        while True:
            if portal_locations:
                for pid, portal in portal_locations.items():
                    msg = f"portal {pid[0]} {pid[1]} {portal[0]} {portal[1]}"
                    send_message(sock, msg)
            if self.player_object:
                pos_msg = f"pos_update {own_address[0]}:{own_address[1]} {self.player_object.center_x} {self.player_object.center_y}"
                send_message(sock, pos_msg)
            time.sleep(0.1)  
                
    def on_update(self, delta_time):
        """ Movement and game logic """

        global game_started, portal_locations
        start_time = timeit.default_timer() # Start the clock

        if(keep_track[own_address] == '2'): # If host
            if not game_started:   
                elapsed_time = time.time() - self.start_time    # time elapsed since game started
                self.countdown = max(0, 5 - int(elapsed_time))  # countdown from 5 to 0
                send_message(sock, f"countdown {self.countdown}")
                if self.countdown == 0:
                    self.countdown = 5
                    game_started = True

        if game_started:
            # Send message to all peers that game has started
            send_message(sock, "game_started")
            self.physics_engine.update() # Update the physics engine
            
        self.countdown = countdown # Update the countdown for non-hosts


        if arcade.check_for_collision_with_list(self.player_object, self.enemy_list): # If player collides with a portal
            for p in self.enemy_list:
                if arcade.check_for_collision(self.player_object, p): # check which portal
                    self.player_object.center_x = self.start_x # teleport player to start
                    self.player_object.center_y = self.start_y
                    for pid, portal in portal_locations.items(): 
                        if p.center_x == portal[0] and p.center_y == portal[1]:
                            portal_locations[pid] = (-1, -1) # delete the portal by marking it as (-1, -1)
                            msg = f"portal {pid[0]} {pid[1]} {-1} {-1}"
                            send_message(sock, msg) # send message to all peers that portal has been disabled
                    p.kill() # remove the portal from the list of portals
                    break

        changed = False

        # Scroll left
        left_bndry = self.view_left + VIEWPORT_MARGIN
        if self.player_object.left < left_bndry:
            self.view_left -= left_bndry - self.player_object.left
            changed = True

        # Scroll right
        right_bndry = self.view_left + SCREEN_WIDTH - VIEWPORT_MARGIN
        if self.player_object.right > right_bndry:
            self.view_left += self.player_object.right - right_bndry
            changed = True

        # Scroll up
        top_bndry = self.view_bottom + SCREEN_HEIGHT - VIEWPORT_MARGIN
        if self.player_object.top > top_bndry:
            self.view_bottom += self.player_object.top - top_bndry
            changed = True

        # Scroll down
        bottom_bndry = self.view_bottom + VIEWPORT_MARGIN
        if self.player_object.bottom < bottom_bndry:
            self.view_bottom -= bottom_bndry - self.player_object.bottom
            changed = True

        if changed:
            arcade.set_viewport(self.view_left,
                                SCREEN_WIDTH + self.view_left,
                                self.view_bottom,
                                SCREEN_HEIGHT + self.view_bottom)
            
        # Save the time it took to do this.
        self.processing_time = timeit.default_timer() - start_time

def send_maze(sock):
    """ Send the maze to all peers """   
    for peer in keep_track:
        if(keep_track[own_address] == '2' and peer != own_address): # If host and not self
            message = f"maze {maze}" # Send the maze
            sock.sendto(message.encode('utf-8'), peer)

def get_host_ip():
    """Automatically determine the local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)) # Google's DNS server
        IP = s.getsockname()[0] #
        s.close()
    except Exception:
        IP = '127.0.0.1'
    return IP

def receive_messages(sock):
    global recv_maze, peer_positions, game_started, countdown, \
        maze, game_won, portal_locations, teleport_x, teleport_y
    
    peer_positions = {}

    while True:
        data, addr = sock.recvfrom(2048)
        message = data.decode('utf-8')

        if message.startswith("maze"):  
            recv_maze = message[5:]
            maze = eval(recv_maze)
        elif message.startswith("countdown"):
            _, count = message.split()
            countdown = int(count)
        elif message.startswith("game_started"):
            game_started = True
        elif message.startswith("status"):
            _, ip, port, status = message.split()
            peer = (ip, int(port))
            keep_track[peer] = status # Update the status of the peer 1 = player, 2 = host, 0 = timed out
        elif message.startswith("pos_update"): 
            _, pid, x, y = message.split()
            ip, port = pid.split(':')
            peer_positions[pid] = (float(x), float(y))
        elif message == "game_won": # If a player has won
            if keep_track[own_address] == '2':  # If host
                maze = create_maze(MAZE_WIDTH, MAZE_HEIGHT)  # Regenerate maze
                send_maze(sock)  # Send new maze to all
            game_won = True
            game_started = False
        elif message.startswith("portal"):
            _, ip, port, x, y = message.split()
            peer = (ip, int(port))
            portal_locations[peer] = (float(x), float(y))
        elif message.startswith("teleport"):
            _, x, y = message.split()
            teleport_x = float(x)
            teleport_y = float(y)
        if addr not in peers:
            # Add the new peer to the list of peers
            peers.append(addr)
            keep_track[addr] = '1'
            print(f"New peer added: {addr}")
            send_maze(sock)
        if(len(peers) == 1): # If there's only one peer
            keep_track[addr] = '2' # Make the peer the host

        last_seen[addr] = time.time() # Update the last seen time of the peer

def send_message(sock, message):
    # send message to self
    if(message.startswith("countdown") or message.startswith("game_won") or message.startswith("portal")):
        sock.sendto(message.encode('utf-8'), own_address)
    # send message to the other peers
    for peer in peers:
        if(peer != own_address):
            sock.sendto(message.encode('utf-8'), peer)

def send_status(sock):
    """ function to let everyone know about everyone else """
    for peer in peers:
        for p in keep_track:
            if(peer != own_address and p != peer): # If not self and not the peer itself
                message = f"status {peer[0]} {peer[1]} {keep_track[peer]}"
                sock.sendto(message.encode('utf-8'), p)
            elif(keep_track[peer] == '2'):
                message = f"status {peer[0]} {peer[1]} {keep_track[peer]}"
                sock.sendto(message.encode('utf-8'), p)

def announce_presence(sock, own_port):
    message = f"hello from {own_port}"
    broadcast_address = '192.168.0.101'  # Ensure this is the correct broadcast address for your network
    sock.sendto(message.encode('utf-8'), (broadcast_address, 6969))

def heartbeat(sock, own_port):
    """ Send a heartbeat message to all peers every 5 seconds to check if they're still alive"""
    while True:
        time.sleep(5)
        send_message(sock, f"heartbeat from {own_port}")
        check_peers()

def check_peers():

    current_time = time.time()
    timeout = 7 # Timeout after 7 seconds
    peers_to_remove = []

    for peer in peers:
        if current_time - last_seen.get(peer, 0) > timeout: # If the peer has timed out
            peers_to_remove.append(peer) 
            keep_track[peer] = '0' # Update the status of the peer to 0
            if peer in last_seen:
                del last_seen[peer]
            print(f"Peer {peer} has timed out and been removed.")

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

    # Find the smallest address from the list of peers and assign it as the host
    smallest_peer = min(peers, key=lambda x: (x[0], x[1]))
    keep_track[smallest_peer] = '2'
    print(f"Updated host to {smallest_peer}")

def update():
    """ Update the host peer every 5 seconds """
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

    """ Create a UDP socket """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Enable broadcasting mode for the socket so we can send messages to all peers
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind((host, port))

    announce_presence(sock, port)
    
    """ Start the threads """
    threading.Thread(target=receive_messages, args=(sock,)).start()
    threading.Thread(target=update, args=()).start()
    threading.Thread(target=handle_user_input, args=(sock,)).start()
    threading.Thread(target=heartbeat, args=(sock, port)).start()

    # If playing from another device (not host) wait 1 sec for the maze to be sent
    time.sleep(1)

    if(keep_track[own_address] == '2'):
        maze = create_maze(MAZE_WIDTH, MAZE_HEIGHT)
    else:
        #convert string to list
        maze = eval(recv_maze) 

    """ Start the game """
    window = MazeN(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, maze, keep_track)
    window.setup()
    arcade.run()

""" Run the main function """
if __name__ == "__main__":
    main()
