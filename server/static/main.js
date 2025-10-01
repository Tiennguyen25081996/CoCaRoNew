const GRID_SIZE = 15;
const boardDiv = document.getElementById("board");
const socket = io();
let winningCells = [];

let mySymbol = null;
let currentTurn = null;
let timer = 30;
let timerInterval = null;

// Tạo bàn cờ và gắn sự kiện click cho từng ô
function createBoard() {
  boardDiv.innerHTML = "";
  for (let y = 0; y < GRID_SIZE; y++) {
    for (let x = 0; x < GRID_SIZE; x++) {
      const cell = document.createElement("div");
      cell.className = "cell";
      cell.dataset.x = x;
      cell.dataset.y = y;
      cell.addEventListener("click", () => {
        if (!mySymbol) {
          alert("Chưa nhận quân từ server, chờ 1 chút.");
          return;
        }
        if (mySymbol !== currentTurn) {
          alert("Chưa đến lượt bạn!");
          return;
        }
        if (cell.textContent && cell.textContent.trim() !== "") {
          alert("Ô này đã có quân rồi.");
          return;
        }
        socket.emit("move", { x: x, y: y });
      });
      boardDiv.appendChild(cell);
    }
  }
}
createBoard();

// gửi join
let playerName = "";
while (!playerName) {
  playerName = prompt("Nhập tên của bạn:");
}
socket.emit("join", { name: playerName });

// nhận symbol khi join
socket.on("joined", (data) => {
  mySymbol = data.symbol;
  alert("Bạn tham gia với quân " + mySymbol);
});

socket.on("quit_confirm", function(data) {
    const fromSid = data.from;
    const modal = document.getElementById("quitModal");
    modal.style.display = "block";

    document.getElementById("btnQuitYes").onclick = function() {
        socket.emit("quit_response", { from: fromSid, accept: true });
        modal.style.display = "none";
    };

    document.getElementById("btnQuitNo").onclick = function() {
        socket.emit("quit_response", { from: fromSid, accept: false });
        modal.style.display = "none";
    };
});


// khi server thông báo tới lượt (player là 'X' hoặc 'O')
socket.on("turn", (data) => {
  currentTurn = data.player;
  const turnInfo = document.getElementById("turn-info");
  if (turnInfo) {
    turnInfo.textContent = (currentTurn === mySymbol) ? `Lượt của bạn (${currentTurn})` : `Lượt của: ${currentTurn}`;
  }
  // reset/khởi động lại timer mỗi khi có turn event
  startTimer();
});

// Lắng nghe event 'move' mà server phát sau khi 1 người đánh
// (app.py hiện tại gửi event 'move' với x,y,player,win). :contentReference[oaicite:2]{index=2}
socket.on("move", (data) => {
  if (!data) return;
  const { x, y, player, win } = data;
  const cell = document.querySelector(`.cell[data-x='${x}'][data-y='${y}']`);
  if (cell) cell.textContent = player;

  if (win) {
    // server cũng phát message và gọi reset; hiển thị tạm
    alert(`${player} thắng!`);
    clearInterval(timerInterval);
  }
});

// Server có thể gửi 'update' với toàn bộ board (ví dụ khi reset hoặc sync)
socket.on("update", data => {
  if (!data || !data.board) return;
  updateBoard(data.board, data.winning_cells || []);
});

// reset game (server gọi reset -> client cập nhật lại bảng)
socket.on("reset", (data) => {
  const b = data && data.board ? data.board : Array.from({length: GRID_SIZE}, () => Array(GRID_SIZE).fill(""));
  updateBoard(b, []);
  const turnInfo = document.getElementById("turn-info");
  if (turnInfo) turnInfo.textContent = "Ván mới bắt đầu!";
  clearInterval(timerInterval);
  const t = document.getElementById("timer");
  if (t) t.textContent = "";
});

// message chung
socket.on("message", data => {
  if (data && data.msg) alert(data.msg);
});

function updateBoard(board, winCells) {
  winningCells = winCells || [];
  document.querySelectorAll(".cell").forEach(cell => {
    const x = parseInt(cell.dataset.x);
    const y = parseInt(cell.dataset.y);
    cell.textContent = (board && board[y] ? (board[y][x] || "") : "");
    cell.classList.remove("win");
  });

  // highlight nếu server gửi vị trí chiến thắng (y,x)
  winningCells.forEach(([y, x]) => {
    const c = document.querySelector(`.cell[data-x='${x}'][data-y='${y}']`);
    if (c) c.classList.add("win");
  });
}

// Timer
function startTimer() {
  clearInterval(timerInterval);
  timer = 30;
  const t = document.getElementById("timer");
  if (t) t.textContent = timer;

  timerInterval = setInterval(() => {
    timer--;
    if (t) t.textContent = timer;
    if (timer <= 0) {
      clearInterval(timerInterval);
      alert("Hết giờ! Bạn mất lượt.");
      // gửi timeout — server hiện tại chưa có handler timeout (nếu cần thêm, mình sẽ hướng dẫn sửa server).
      socket.emit("timeout");
    }
  }, 1000);
}

// quit / reset helpers
function quitGame() { socket.emit("quit_request"); }

function resetBoard() { socket.emit("reset"); }

