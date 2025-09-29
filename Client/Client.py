# client.py
import pygame
import socket
import json

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, BG_COLOR, CELL_SIZE, GRID_SIZE

HOST = '192.168.23.82'
PORT = 8080

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Cờ Caro LAN")
clock = pygame.time.Clock()

board = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
player = 'X'

running = True
while running:
    screen.fill(BG_COLOR)

    # draw grid
    for x in range(GRID_SIZE):
        pygame.draw.line(screen, (0,0,0), (x*CELL_SIZE,0), (x*CELL_SIZE, SCREEN_HEIGHT))
    for y in range(GRID_SIZE):
        pygame.draw.line(screen, (0,0,0), (0,y*CELL_SIZE), (SCREEN_WIDTH, y*CELL_SIZE))

    # draw pieces
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if board[y][x] == 'X':
                pygame.draw.line(screen, (255,0,0), (x*CELL_SIZE+10, y*CELL_SIZE+10),
                                 (x*CELL_SIZE+CELL_SIZE-10, y*CELL_SIZE+CELL_SIZE-10),2)
                pygame.draw.line(screen, (255,0,0), (x*CELL_SIZE+CELL_SIZE-10, y*CELL_SIZE+10),
                                 (x*CELL_SIZE+10, y*CELL_SIZE+CELL_SIZE-10),2)
            elif board[y][x] == 'O':
                pygame.draw.circle(screen, (0,0,255), (x*CELL_SIZE+CELL_SIZE//2, y*CELL_SIZE+CELL_SIZE//2), CELL_SIZE//2-10,2)

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            x, y = mx//CELL_SIZE, my//CELL_SIZE
            move = {"x": x, "y": y, "player": player}
            client.sendall(json.dumps(move).encode())
            data = client.recv(4096).decode()
            board = json.loads(data)

pygame.quit()