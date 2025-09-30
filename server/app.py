from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

GRID_SIZE = 15
board = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
current_player = "X"
winning_cells = []
players = {}

def check_win(player):
    global winning_cells
    winning_cells = []
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if board[y][x] != player:
                continue
            # Horizontal
            if x <= GRID_SIZE-5 and all(board[y][x+i] == player for i in range(5)):
                winning_cells = [(y, x+i) for i in range(5)]
                return True
            # Vertical
            if y <= GRID_SIZE-5 and all(board[y+i][x] == player for i in range(5)):
                winning_cells = [(y+i, x) for i in range(5)]
                return True
            # Diagonal \
            if x <= GRID_SIZE-5 and y <= GRID_SIZE-5 and all(board[y+i][x+i] == player for i in range(5)):
                winning_cells = [(y+i, x+i) for i in range(5)]
                return True
            # Diagonal /
            if x >= 4 and y <= GRID_SIZE-5 and all(board[y+i][x-i] == player for i in range(5)):
                winning_cells = [(y+i, x-i) for i in range(5)]
                return True
    return False

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("move")
def handle_move(data):
    global current_player
    x, y = data["x"], data["y"]
    if board[y][x] == "":
        board[y][x] = current_player
        win = check_win(current_player)
        emit("update", {"board": board, "win": win, "winning_cells": winning_cells}, broadcast=True)
        current_player = "O" if current_player == "X" else "X"
        socketio.emit("reset_timer")

@socketio.on("reset")
def handle_reset():
    global board, current_player, winning_cells
    board = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    current_player = "X"
    winning_cells = []
    emit("update", {"board": board, "win": False, "winning_cells": []}, broadcast=True)

@socketio.on("connect")
def handle_connect():
    print(f"Client {request.sid} connected")

@socketio.on("join")
def handle_join(data):
    name = data.get("name", f"Player{len(players)+1}")
    players[request.sid] = name
    emit("message", {"msg": f"{name} đã tham gia."}, broadcast=True, include_self=False)

@socketio.on("disconnect")
def handle_disconnect():
    if request.sid in players:
        name = players[request.sid]
        del players[request.sid]

        emit("message", {"msg": f"{name} đã thoát. Bạn thắng!"}, broadcast=True, include_self=False)

        global board, current_player
        board = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        current_player = "X"
        socketio.emit("reset", {"board": board})


@socketio.on("quit_request")
def handle_quit_request():
    # gửi yêu cầu quit tới tất cả client khác
    emit("quit_confirm", {"from": request.sid}, broadcast=True, include_self=False)


@socketio.on("quit_response")
def handle_quit_response(data):
    # data = {"from": "...", "accept": True/False}
    if data["accept"]:
        # Reset game và gửi thông báo thắng/thua
        global board, current_player, winning_cells
        board = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        current_player = "X"
        winning_cells = []
        emit("update", {"board": board, "win": False, "winning_cells": []}, broadcast=True)
        emit("message", {"msg": "Bạn đã thua."}, to=data["from"])
        emit("message", {"msg": "Bạn đã thắng!"}, to=request.sid)
    else:
        emit("message", {"msg": "Đối thủ không đồng ý kết thúc game."}, to=data["from"])

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)