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

function resetBoard() {
    socket.emit("reset");
}