const GRID_SIZE = 15;
const boardDiv = document.getElementById("board");
const socket = io();
let winningCells = [];

// Initialize board
for (let y = 0; y < GRID_SIZE; y++) {
    for (let x = 0; x < GRID_SIZE; x++) {
        const cell = document.createElement("div");
        cell.className = "cell";
        cell.dataset.x = x;
        cell.dataset.y = y;
        cell.addEventListener("click", () => {
            socket.emit("move", {x: x, y: y});
        });
        boardDiv.appendChild(cell);
    }
}

let playerName = "";
while (!playerName) {
  playerName = prompt("Nhập tên của bạn:");
}
socket.emit("join", { name: playerName });

socket.on("update", data => {
    updateBoard(data.board, data.winning_cells);
    if (data.win) alert("Player wins!");
});

function updateBoard(board, winCells) {
    winningCells = winCells;
    document.querySelectorAll(".cell").forEach(cell => {
        const x = parseInt(cell.dataset.x);
        const y = parseInt(cell.dataset.y);
        cell.textContent = board[y][x];
        cell.classList.remove("win");
    });
    // Highlight winning cells
    winningCells.forEach(([y,x]) => {
        document.querySelector(`.cell[data-x='${x}'][data-y='${y}']`).classList.add("win");
    });
}

function quitGame() {
    socket.emit("quit_request");
}

// Khi đối thủ bấm quit
socket.on("quit_confirm", data => {
    const accept = confirm("Đối thủ muốn thoát game. Bạn có đồng ý không?");
    socket.emit("quit_response", { from: data.from, accept: accept });
});

// Hiện thông báo kết quả
socket.on("message", data => {
    alert(data.msg);
});

function resetBoard() {
    socket.emit("reset");
}