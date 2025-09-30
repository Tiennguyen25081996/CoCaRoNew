from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

players = {}   # sid -> {"name":..., "symbol":...}
symbols = ["X", "O"]
board = [["" for _ in range(15)] for _ in range(15)]
current_turn = None

def reset_board():
    global board, current_turn
    board = [["" for _ in range(15)] for _ in range(15)]
    current_turn = None

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("join")
def on_join(data):
    global current_turn
    sid = data["sid"]
    name = data["name"]

    if len(players) < 2:
        symbol = symbols[len(players)]
        players[sid] = {"name": name, "symbol": symbol}
        emit("assign_symbol", {"symbol": symbol})
        emit("message", {"msg": f"{name} đã tham gia với quân {symbol}"}, broadcast=True)

        # Khi đủ 2 người chơi thì bắt đầu
        if len(players) == 2 and current_turn is None:
            current_turn = symbols[0]
            emit("turn", {"player": current_turn, "name": get_name_by_symbol(current_turn)}, broadcast=True)
    else:
        emit("message", {"msg": "Phòng đã đầy, không thể tham gia."})

@socketio.on("move")
def on_move(data):
    global current_turn
    x, y = data["x"], data["y"]
    sid = data["sid"]
    player = players[sid]["symbol"]

    if player != current_turn:
        return  # không đúng lượt
    if board[x][y] != "":
        return  # ô đã đánh

    board[x][y] = player
    emit("update", {"x": x, "y": y, "player": player}, broadcast=True)

    # kiểm tra thắng
    if check_win(x, y, player):
        emit("message", {"msg": f"{players[sid]['name']} đã thắng!"}, broadcast=True)
        reset_board()
        return

    # chuyển lượt
    current_turn = "O" if current_turn == "X" else "X"
    emit("turn", {"player": current_turn, "name": get_name_by_symbol(current_turn)}, broadcast=True)

@socketio.on("timeout")
def on_timeout(data):
    sid = data["sid"]
    loser_symbol = players[sid]["symbol"]
    loser_name = players[sid]["name"]

    winner_symbol = "O" if loser_symbol == "X" else "X"
    winner_name = get_name_by_symbol(winner_symbol)

    emit("message", {"msg": f"{loser_name} hết giờ! {winner_name} thắng!"}, broadcast=True)
    reset_board()

@socketio.on("disconnect")
def on_disconnect():
    sid = None
    for k in list(players.keys()):
        if players[k]:
            sid = k
            break

    if sid and sid in players:
        loser_name = players[sid]["name"]
        players.pop(sid)
        emit("message", {"msg": f"{loser_name} đã thoát, bạn còn lại thắng!"}, broadcast=True)
        reset_board()

def get_name_by_symbol(symbol):
    for p in players.values():
        if p["symbol"] == symbol:
            return p["name"]
    return "?"

def check_win(x, y, sym):
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    for dx, dy in directions:
        count = 1
        for d in [1, -1]:
            nx, ny = x, y
            while True:
                nx += dx * d
                ny += dy * d
                if 0 <= nx < 15 and 0 <= ny < 15 and board[nx][ny] == sym:
                    count += 1
                else:
                    break
        if count >= 5:
            return True
    return False

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)
