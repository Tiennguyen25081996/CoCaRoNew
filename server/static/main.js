const GRID_SIZE = 15;
const boardDiv = document.getElementById("board");
const socket = io();
let winningCells = [];

let mySymbol = null;
let currentTurn = null;

// Tạo bàn cờ 15x15
for (let y = 0; y < GRID_SIZE; y++) {
    for (let x = 0; x < GRID_SIZE; x++) {
        const cell = document.createElement("div");
        cell.className = "cell";
        cell.dataset.x = x;
        cell.dataset.y = y;
        cell.addEventListener("click", () => {
            // chỉ được đánh khi đến lượt
            if (mySymbol !== currentTurn) {
                alert("Chưa đến lượt bạn!");
                return;
            }
            socket.emit("move", {x: x, y: y});
        });
        boardDiv.appendChild(cell);
    }
}

// Hỏi tên khi join
let playerName = "";
while (!playerName) {
  playerName = prompt("Nhập tên của bạn:");
}
socket.emit("join", { name: playerName });

// Nhận thông tin khi tham gia
socket.on("joined", (data) => {
    mySymbol = data.symbol;
    alert("Bạn tham gia với quân " + mySymbol);
});

// Cập nhật lượt chơi
socket.on("turn", (data) => {
    currentTurn = data.player;
    document.getElementById("turn-info").textContent =
        "Lượt của: " + data.name + " (" + data.player + ")";
});

// Đồng hồ đếm ngược 30s
let timer = 30;
let timerInterval;
function startTimer() {
    clearInterval(timerInterval);
    timer = 30;
    document.getElementById("timer").textContent = timer;

    timerInterval = setInterval(() => {
        timer--;
        document.getElementById("timer").textContent = timer;

        if (timer <= 0) {
            clearInterval(timerInterval);
            alert("Hết giờ! Bạn mất lượt.");
            socket.emit("timeout");
        }
    }, 1000);
}
socket.on("reset_timer", () => startTimer());

// Nhận update bàn cờ
socket.on("update", data => {
    updateBoard(data.board, data.winning_cells);
    if (data.win) {
        alert("Có người thắng!");
    }
});

function updateBoard(board, winCells) {
    winningCells = winCells;
    document.querySelectorAll(".cell").forEach(cell => {
        const x = parseInt(cell.dataset.x);
        const y = parseInt(cell.dataset.y);
        cell.textContent = board[y][x];
        cell.classList.remove("win");
    });
    // Highlight đường thắng
    winningCells.forEach(([y, x]) => {
        document.querySelector(`.cell[data-x='${x}'][data-y='${y}']`)
            .classList.add("win");
    });
}

// Xử lý quit game
function quitGame() {
    socket.emit("quit_request");
}

socket.on("quit_confirm", data => {
    const accept = confirm("Đối thủ muốn thoát game. Bạn có đồng ý không?");
    socket.emit("quit_response", { from: data.from, accept: accept });
});

// Hiện thông báo kết quả
socket.on("message", data => {
    alert(data.msg);
});

// Reset ván mới
function resetBoard() {
    socket.emit("reset");
}
