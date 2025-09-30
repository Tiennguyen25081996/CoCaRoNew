from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

GRID_SIZE = 15
board = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
winning_cells = []
players = {}              # {sid: name}
player_symbols = {}       # {sid: "X" hoặc "O"}
current_player = None


def check_win(player):
    """Kiểm tra thắng 5 quân liên tiếp"""
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


def reset_board(first_player=None):
    """Reset bàn cờ"""
    global board, current_player, winning_cells
    board = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    current_player = first_player
    winning_cells = []
    socketio.emit("update", {"board": board, "winning_cells": [], "win": False})


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("join")
def handle_join(data):
    global current_player

    name = data.get("name", f"Player{len(players)+1}")
    sid = request.sid

    if len(players) >= 2:
        emit("message", {"msg": "Phòng đã đủ 2 người, bạn chỉ có thể xem."})
        return

    players[sid] = name
    symbol = "X" if len(players) == 1 else "O"
    player_symbols[sid] = symbol

    emit("joined", {"name": name, "symbol": symbol})
    emit("message", {"msg": f"{name} đã tham gia với quân {symbol}."},
         broadcast=True, include_self=False)

    if len(players) == 2:
        # X đi trước
        for s, sym in player_symbols.items():
            if sym == "X":
                current_player = s
                socketio.emit("turn", {"player": sym, "name": players[s]})
                break


@socketio.on("move")
def handle_move(data):
    global current_player

    sid = request.sid
    if sid not in players:
        return

    if len(players) < 2:
        emit("message", {"msg": "Chưa đủ 2 người chơi để bắt đầu."})
        return

    if sid != current_player:
        emit("message", {"msg": "Không phải lượt của bạn!"})
        return

    x, y = data["x"], data["y"]
    symbol = player_symbols[sid]

    if board[y][x] == "":
        board[y][x] = symbol
        win = check_win(symbol)

        socketio.emit("update", {
            "board": board,
            "winning_cells": winning_cells,
            "win": win
        })

        if win:
            socketio.emit("message", {"msg": f"{players[sid]} thắng!"})
            reset_board()
        else:
            # đổi lượt
            next_sid = [s for s in players if s != sid][0]
            current_player = next_sid
            socketio.emit("turn", {"player": player_symbols[next_sid],
                                   "name": players[next_sid]})


@socketio.on("reset")
def handle_reset():
    reset_board(first_player="X")


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    if sid in players:
        name = players[sid]
        del players[sid]
        player_symbols.pop(sid, None)

        emit("message", {"msg": f"{name} đã thoát. Bạn thắng!"},
             broadcast=True, include_self=False)

        reset_board()


@socketio.on("quit_request")
def handle_quit_request():
    emit("quit_confirm", {"from": request.sid},
         broadcast=True, include_self=False)


@socketio.on("quit_response")
def handle_quit_response(data):
    if data["accept"]:
        reset_board(first_player="X")
        emit("message", {"msg": "Bạn đã thua."}, to=data["from"])
        emit("message", {"msg": "Bạn đã thắng!"}, to=request.sid)
    else:
        emit("message", {"msg": "Đối thủ không đồng ý kết thúc game."},
             to=data["from"])


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)
