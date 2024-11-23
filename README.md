# MazeN
MazeN ("Amazing") is a multiplayer maze game by [Vlad Dobrescu](https://github.com/vlad-dobrescu) and [Alesia Vlasiu](https://github.com/alesia-vlasiu), written entirely in Python.

---

## Game Description
Players can start a new game (as host) or join an existing one by entering a connected player's address and port. Players spawn in the top-left corner of a randomly generated maze, aiming to reach the bottom-right corner. When a player wins, the game restarts with a new maze.

---

## Networking Features
- **Peer-to-Peer network**  
- **Host migration**  
- **Lock-step simulation**  
- **UDP Protocol**  

---

## Game Features
- **Movement:** Use "W, A, S, D" or arrow keys.  
- **Countdown Timer:** A countdown at the start lets players join before the game begins, with restricted movement during this time.  
- **Portals:**  
  - Press spacebar to place one portal per match (a subtle square).  
  - **Portal Collision:** Opponents colliding with your portal are teleported back to the start.  
  - **Destroy Portals:** Stand on a portal and press "X" to destroy it, teleporting its creator to the portal's location.  
- **Maze Generation:** Randomized Depth-First Search algorithm ensures unique mazes.  
- **Peer Count:** Displays the number of connected peers in the top-left corner.  
- **Hide Opponents:** Press "I" to hide opponents for smoother gameplay.

---

## Game Preview
### Portal Feature
[![Watch the video](https://img.youtube.com/vi/Y4PRZb1RI3s/0.jpg)](https://www.youtube.com/watch?v=Y4PRZb1RI3s)



### Maze Reset After Win
[![Watch the video](https://img.youtube.com/vi/ZVSG6uoRkfw/0.jpg)](https://youtu.be/ZVSG6uoRkfw)

---

## Setup

1. Install Python Arcade:
   ```bash
   pip install arcade
   ```
2. Clone this repository.
3. Run the game:
   ```bash
   python net.py
   ```
