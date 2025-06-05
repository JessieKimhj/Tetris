# Python Multiplayer Tetris

A real-time multiplayer Tetris game implemented using WebSocket and Flask. Players can compete against each other in this browser-based version of the classic game.

## Technical Stack

- Backend:
  - Python
  - Flask (Web Server)
  - WebSocket (Real-time Communication)
  - NumPy (Game Logic)

- Frontend:
  - HTML
  - JavaScript
  - CSS

### Prerequisites

- Python 3.x
- pip (Python package manager)

### Installation & Running the Game for MacOS

```bash
pip install flask websockets numpy
python tetris_server.py --host 0.0.0.0
```
### On the 2nd Terminal
```bash
python -m flask --app start run --host=0.0.0.0
```
The `--host 0.0.0.0` flag allows the server to accept connections from any IP address, not just localhost. This is necessary for:

- Allowing other devices on the network to connect to your server

Without this flag, the server would only accept connections from localhost (127.0.0.1), making it impossible for other players to join.


