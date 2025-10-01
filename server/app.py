from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

GRID_SIZE = 15
board = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
winning_cells = []
players = {}              # {sid: name}
player_symbols = {}       # {sid: "X" hoặc "O"}
current_player = None

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

        socketio.emit("move", {"x": x, "y": y, "player": symbol, "win": win})

        if win:
            socketio.emit("message", {"msg": f"{players[sid]} thắng!"})
            reset_board()
            socketio.emit("update", {"board": board, "win": False, "winning_cells": []})
        else:
            next_sid = [s for s in players if s != sid][0]
            current_player = next_sid
            socketio.emit("turn", {"player": player_symbols[next_sid]})


@socketio.on("reset")
def handle_reset():
    reset_board()
    emit("update", {"board": board, "win": False, "winning_cells": []}, broadcast=True)

@socketio.on("connect")
def handle_connect():
    logger.info(f"Client {request.sid} connected")

@socketio.on("join")
def handle_join(data):
    global current_player

    name = data.get("name", f"Player{len(players)+1}")
    sid = request.sid

    if len(players) >= 2:
        emit("message", {"msg": "Phòng đã đủ người, bạn chỉ có thể xem."})
        return

    players[sid] = name
    symbol = "X" if len(players) == 1 else "O"
    player_symbols[sid] = symbol

    emit("joined", {"name": name, "symbol": symbol})  # gửi riêng cho client mới join
    emit("message", {"msg": f"{name} đã tham gia với quân {symbol}."}, broadcast=True, include_self=False)

    if len(players) == 2:
        # chọn X đi trước
        for s, sym in player_symbols.items():
            if sym == "X":
                current_player = s
                socketio.emit("turn", {"player": sym})
                break
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

        if len(players) == 2:
            for sid, pname in players.items():
                if pname != name:  # chọn người còn lại
                    current_player = sid
                    socketio.emit("turn", {"player": player_symbols[sid]})
                    break

@socketio.on("quit_request")
def handle_quit_request():
    requester = request.sid
    opponents = [sid for sid in players if sid != requester]

    if opponents:
        opponent_sid = opponents[0]
        emit("quit_confirm", {"from": requester}, to=opponent_sid)


@socketio.on("quit_response")
def handle_quit_response(data):
    global current_player, board
    logger.info(f"quit_response: {data}")

    if data.get("accept", False):
        # 1. Reset board dữ liệu
        reset_board()

        # 2. Gửi cập nhật board mới cho tất cả
        socketio.emit("update", {"board": board, "win": False, "winning_cells": []})

        # 3. Thông báo kết quả
        emit("message", {"msg": "Bạn đã thua."}, to=data["from"])
        emit("message", {"msg": "Bạn đã thắng!"}, to=request.sid)

        # 4. Nếu vẫn còn 2 người chơi -> chọn lại X đi trước
        if len(players) == 2:
            for sid, sym in player_symbols.items():
                if sym == "X":
                    current_player = sid
                    socketio.emit("turn", {"player": sym})
                    break

        logger.info(f"Game reset xong, current_player = {current_player}, len(player_symbols) = {len(player_symbols)}")

    else:
        emit("message", {"msg": "Đối thủ không đồng ý kết thúc game."}, to=data["from"])

def reset_board():
    global board, current_player, winning_cells
    board = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    current_player = None
    winning_cells = []
    return board

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)