let socket = io();
let mySymbol = null;
let currentTurn = null;
let sid = null;
let timerInterval = null;
let timeLeft = 30;

// nhập tên khi join
let playerName = prompt("Nhập tên của bạn:");
socket.emit("join", { sid: socket.id, name: playerName });

// nhận ký hiệu
socket.on("assign_symbol", (data) => {
    mySymbol = data.symbol;
    document.getElementById("player-info").textContent =
        "Bạn là: " + mySymbol;
});

// cập nhật lượt
socket.on("turn", (data) => {
    currentTurn = data.player;
    document.getElementById("turn-info").textContent =
        "Lượt của: " + data.name + " (" + data.player + ")";

    if (currentTurn === mySymbol) {
        startTimer();
    } else {
        stopTimer();
    }
});

// cập nhật board
socket.on("update", (data) => {
    let cell = document.getElementById(`cell-${data.x}-${data.y}`);
    cell.textContent = data.player;
});

// thông báo
socket.on("message", (data) => {
    alert(data.msg);
    stopTimer();
});

// click cell
function makeMove(x, y) {
    if (currentTurn !== mySymbol) return; // không đúng lượt
    socket.emit("move", { x: x, y: y, sid: socket.id });
}

// timer
function startTimer() {
    stopTimer();
    timeLeft = 30;
    document.getElementById("timer").textContent = timeLeft;

    timerInterval = setInterval(() => {
        timeLeft--;
        document.getElementById("timer").textContent = timeLeft;
        if (timeLeft <= 0) {
            stopTimer();
            socket.emit("timeout", { sid: socket.id });
        }
    }, 1000);
}

function stopTimer() {
    clearInterval(timerInterval);
    document.getElementById("timer").textContent = "";
}
