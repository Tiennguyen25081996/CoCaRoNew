from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

GRID_SIZE = 15
board = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
current_player = "X"

def check_win(player):
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if board[y][x] != player:
                continue
            # Horizontal
            if x <= GRID_SIZE-5 and all(board[y][x+i] == player for i in range(5)):
                return True
            # Vertical
            if y <= GRID_SIZE-5 and all(board[y+i][x] == player for i in range(5)):
                return True
            # Diagonal \
            if x <= GRID_SIZE-5 and y <= GRID_SIZE-5 and all(board[y+i][x+i] == player for i in range(5)):
                return True
            # Diagonal /
            if x >= 4 and y <= GRID_SIZE-5 and all(board[y+i][x-i] == player for i in range(5)):
                return True
    return False

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/move", methods=["POST"])
def move():
    global current_player
    data = request.json
    x, y = data["x"], data["y"]
    if board[y][x] == "":
        board[y][x] = current_player
        win = check_win(current_player)
        current_player = "O" if current_player == "X" else "X"
        return jsonify({"board": board, "win": win})
    return jsonify({"board": board, "win": False})

@app.route("/board", methods=["GET"])
def get_board():
    return jsonify({"board": board})

@app.route("/reset", methods=["POST"])
def reset():
    global board, current_player
    board = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    current_player = "X"
    return jsonify({"board": board})
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)