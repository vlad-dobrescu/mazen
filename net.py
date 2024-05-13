import socket
import threading
import time
import arcade
import random
import timeit
import os


OBJ_SIZE = 64
OBJ_SCALE = 0.5

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Maze Game"

MOVEMENT_SPEED = 8
CELL_EMPTY = 0
CELL_FULL  = 1
MAZE_HEIGHT = 21
MAZE_WIDTH = 21
VIEWPORT_MARGIN = 200

def create_grid(width, height):
    """ Create a grid with empty cells on odd row/column combinations. """
    grid = []
    for row in range(height):
        grid.append([])
        for column in range(width):
            if column % 2 == 1 and row % 2 == 1:
                grid[row].append(CELL_FULL)
            elif column == 0 or row == 0 or column == width - 1 or row == height - 1:
                grid[row].append(CELL_FULL)
            else:
                grid[row].append(CELL_FULL)
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
                maze[path_row][path_col] = CELL_EMPTY
            # Check if the movement is horizontal
            elif next_y == y:
                # Calculate the row index for the path
                path_row = y * 2 + 1
                # Calculate the column index for the path
                path_col = max(x, next_x) * 2
                # Set the path cell to empty
                maze[path_row][path_col] = CELL_EMPTY

            
            # Recursively visit the next cell
            walk(next_x, next_y)

    # Start the maze generation from a random cell within the grid
    walk(random.randrange(cells_wide), random.randrange(cells_high))

    return maze


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
    while True:
        data, addr = sock.recvfrom(2048)
        message = data.decode('utf-8')
        #print(f"Received message from {addr}: {message}")
        if message.startswith("maze"):
            #strip message to "maze " and the rest 
            maze = message[5:]
            print(f"Received maze from {addr}: {maze}")
        if message.startswith("status"):
            _, ip, port, status = message.split()
            peer = (ip, int(port))
            keep_track[peer] = status
            #print(f"Status update from {peer}: {status}   pllllll")
        if addr not in peers:
            peers.append(addr)
            keep_track[addr] = '1'
            print(f"New peer added: {addr}")
        last_seen[addr] = time.time()

def send_message(sock, message):
    for peer in peers:
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
    current_host = [peer for peer, status in keep_track.items() if status == '2']
    if current_host:
        return  # If there's already a host, no need to update

    if not peers:
        print("No peers left to assign host.")
        return

    # Find the smallest address from the list of peers
    smallest_peer = min(peers, key=lambda x: (x[0], x[1]))
    keep_track[smallest_peer] = '2'
    print(f"Updated host to {smallest_peer}")

       

def main():
    host = get_host_ip()
    port = int(input("Enter your port number: "))

    #broadcast_address = input("Enter the adress you want to connect to (Type 0 if none): ")
    #broadcast_port = input("Enter the port you want to connect to (Type 0 if none): ")

    global peers, last_seen, keep_track, own_address, sock
    own_address = (host, port)
    keep_track = {(host, port): '1'}
    peers = [(host, port)]
    last_seen = {(host, port): time.time()}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind((host, port))

    announce_presence(sock, port)

    threading.Thread(target=receive_messages, args=(sock,)).start()
    threading.Thread(target=handle_user_input, args=(sock,)).start()
    threading.Thread(target=heartbeat, args=(sock, port)).start()


    while True:
        time.sleep(5)
        update_host_peer()
        send_status(sock)
        for peer in peers:
            for p in keep_track:
                if(keep_track[p] == '2'):
                    maze = create_maze(MAZE_WIDTH, MAZE_HEIGHT)
                    #print(f"Creating maze: {maze}")
                    if(peer != p and peer != own_address):
                        message = f"maze {maze}"
                        sock.sendto(message.encode('utf-8'), peer)
                        print(f"Sending {maze} to {peer}")


if __name__ == "__main__":
    main()


    



