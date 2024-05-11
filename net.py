import socket
import threading
import time

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
        data, addr = sock.recvfrom(1024)
        message = data.decode('utf-8')
        #print(f"Received message from {addr}: {message}")
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
    timeout = 15
    for peer in list(peers):
        if current_time - last_seen.get(peer, 0) > timeout:
            peers.remove(peer)
            if(keep_track[peer] == '2'):    #if the peer is host
                keep_track[own_address] = '2'   #set self to host

            keep_track[peer] = '0'
            if peer in last_seen:
                del last_seen[peer]
            print(f"Peer {peer} has timed out and been removed.")

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

def update_host_peer(sock, keep_track):
    #if the only thing in keep_track is self
    if len(keep_track) == 1:
        keep_track[own_address] = '2' #set self to host
        print(f"Updated self to host")
       

def main():
    host = get_host_ip()
    port = int(input("Enter port number: "))

    global peers, last_seen, keep_track, own_address
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
        update_host_peer(sock, keep_track)
        send_status(sock)

if __name__ == "__main__":
    main()
