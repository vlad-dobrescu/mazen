import socket
import threading
import time

# Predefined list of potential peer ports
potential_peers = [5001, 5002, 5003]


def get_host_ip():
    """Automatically determine the local IP address."""
    try:
        # This creates a temporary connection to an Internet IP to find the interface used for the Internet connection
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Google DNS server IP and port
        IP = s.getsockname()[0]
        s.close()
    except Exception:
        IP = '127.0.0.1'  # Fallback to localhost if the network is unreachable
    return IP
# Function to handle incoming messages
def receive_messages(sock):
    while True:
        data, addr = sock.recvfrom(1024)  # Buffer size is 1024 bytes
        message = data.decode('utf-8')
        print(f"Received message from {addr}: {message}")
        if addr not in peers:
            peers.append(addr)
            print(f"New peer added: {addr}")
        last_seen[addr] = time.time()  # Update the last seen time for the peer

# Function to send a message to all peers
def send_message(sock, message):
    for peer in peers:
        sock.sendto(message.encode('utf-8'), peer)

# Function to announce the presence of this peer to potential peers
def announce_presence(sock, own_port):
    message = f"hello from {own_port}"
    broadcast_address = '192.168.0.101'  # Adjust to your local network's broadcast address
    for port in potential_peers:
        if port != own_port:
            sock.sendto(message.encode('utf-8'), (broadcast_address, port))


# Heartbeat function to periodically check peer availability
def heartbeat(sock, own_port):
    while True:
        time.sleep(5)  # Send a heartbeat every 5 seconds
        send_message(sock, f"heartbeat from {own_port}")
        check_peers()  # Check for any peers that should be timed out

# Check for peers that have timed out
def check_peers():
    current_time = time.time()
    timeout = 15  # Time in seconds after which we consider a peer dead if no heartbeat received
    for peer in list(peers):
        if current_time - last_seen.get(peer, 0) > timeout:
            if peer in peers:
                peers.remove(peer)
            if peer in last_seen:
                del last_seen[peer]
            print(f"Peer {peer} has timed out and been removed.")

# Function to handle user input
def handle_user_input(sock):
    while True:
        command = input("Enter command (send <message>, list): ")
        if command.startswith("send "):
            message = command[5:]
            send_message(sock, message)
        elif command == "list":
            print("Connected peers:")
            for peer in peers:
                print(f"Peer: {peer}")

# Main function to set up the peer
def main():
    host = get_host_ip()
    port = int(input("Enter port number for this peer: "))
    own_address = (host, port)
    global peers, last_seen
    peers = [own_address]  # Start with own address
    last_seen = {own_address: time.time()}  # Initialize last seen for self

    # Creating a socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(own_address)

    # Announce presence to other potential peers
    announce_presence(sock, port)

    # Starting threads for handling incoming messages, user input, and heartbeats
    threading.Thread(target=receive_messages, args=(sock,)).start()
    threading.Thread(target=handle_user_input, args=(sock,)).start()
    threading.Thread(target=heartbeat, args=(sock, port)).start()


if __name__ == "__main__":
    main()
