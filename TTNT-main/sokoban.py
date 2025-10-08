
import sys
import pygame
import string
import queue
import copy
import time
from pygame.locals import *

TIME_LIMITED = 1800
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60


class Game:
     # Kiểm tra giá trị hợp lệ của từng ô trong bản đồ trò chơi
    def is_valid_value(self,char):
        if ( char == ' ' or #khoảng trắng
            char == '#' or #tường
            char == '@' or #người chơi
            char == '.' or #đích
            char == '*' or #thùng hoặc đích
            char == '$' or #thùng
            char == '+' ): #người chơi đứng trên đích
            return True
        else:
            print("LỖI: Giá trị được thêm vào không hợp lệ")
            return False

    def __init__(self, matrix):#khởi tạo các giá trị
        self.heuristic = 0  # Giá trị heuristics (được dùng trong A* search)
        self.pathSol = ""  # Lưu đường đi để tìm ra lời giải
        self.stack = []  # Stack lưu các bước di chuyển để có thể quay lại
        self.matrix = matrix  # Lưu trạng thái của bản đồ trò chơi

    def __lt__(self, other): 
        return self.heuristic < other.heuristic

    def load_size(self):
        x = 0
        y = len(self.matrix)
        for row in self.matrix:
            if len(row) > x:
                x = len(row)
        return (x * 64, y * 64)

    def get_matrix(self): # Lấy trạng thái của bản đồ trò chơi
        return self.matrix

    def print_matrix(self): # In ma trận trạng thái ra màn hình console
        for row in self.matrix:
            for char in row:
                sys.stdout.write(char)
                sys.stdout.flush()
            sys.stdout.write('\n')

    def get_content(self,x,y):  # Lấy nội dung tại một vị trí (x, y) cụ thể
        return self.matrix[y][x]

    def set_content(self,x,y,content):# Đặt giá trị mới vào vị trí (x, y)
        if self.is_valid_value(content):
            self.matrix[y][x] = content
        else:
             print("LỖI: Giá trị '"+content+"' được thêm vào không hợp lệ")

    def worker(self): # Tìm vị trí hiện tại của người chơi (@ hoặc +)
        x = 0
        y = 0
        for row in self.matrix:
            for pos in row:
                if pos == '@' or pos == '+':
                    return (x, y, pos)
                else:
                    x = x + 1
            y = y + 1
            x = 0

    def box_list(self): # Tìm danh sách vị trí của các hộp ($)
        x = 0
        y = 0
        boxList = []
        for row in self.matrix:
            for pos in row:
                if pos == '$':
                    boxList.append((x,y))
                x = x + 1
            y = y + 1
            x = 0
        return boxList

    def dock_list(self): # Tìm danh sách vị trí của các điểm đích (.)
        x = 0
        y = 0
        dockList = []
        for row in self.matrix:
            for pos in row:
                if pos == '.':
                    dockList.append((x,y))
                x = x + 1
            y = y + 1
            x = 0
        return dockList

    def can_move(self,x,y): # Kiểm tra người chơi có thể di chuyển đến ô (x, y) hay không
        return self.get_content(self.worker()[0]+x,self.worker()[1]+y) not in ['#','*','$']

    def next(self,x,y): # Lấy nội dung của ô tiếp theo nếu người chơi di chuyển đến đó
        return self.get_content(self.worker()[0]+x,self.worker()[1]+y)

    def can_push(self,x,y):  # Kiểm tra xem có thể đẩy hộp khôn
        return (self.next(x,y) in ['*','$'] and self.next(x+x,y+y) in [' ','.'])

    def is_completed(self): # Kiểm tra xem trò chơi đã hoàn thành chưa (tất cả hộp đã nằm trên điểm đích)
        for row in self.matrix:
            for cell in row:
                if cell == '$':
                    return False
        return True

    def move_box(self,x,y,a,b):  # Di chuyển hộp theo hướng cụ thể
#        (x,y) -> người chơi di chuyển
#        (a,b) -> thùng di chuyển
        current_box = self.get_content(x,y)
        future_box = self.get_content(x+a,y+b)
        if current_box == '$' and future_box == ' ':
            self.set_content(x+a,y+b,'$')
            self.set_content(x,y,' ')
        elif current_box == '$' and future_box == '.':
            self.set_content(x+a,y+b,'*')
            self.set_content(x,y,' ')
        elif current_box == '*' and future_box == ' ':
            self.set_content(x+a,y+b,'$')
            self.set_content(x,y,'.')
        elif current_box == '*' and future_box == '.':
            self.set_content(x+a,y+b,'*')
            self.set_content(x,y,'.')

    def unmove(self):  
        if len(self.stack) > 0:
            movement = self.stack.pop()
            if movement[2]:
                current = self.worker()
                self.move(movement[0] * -1,movement[1] * -1, False)
                self.move_box(current[0]+movement[0],current[1]+movement[1],movement[0] * -1,movement[1] * -1)
            else:
                self.move(movement[0] * -1,movement[1] * -1, False)

    def move(self,x,y,save):  # Thực hiện bước di chuyển của người chơi, có thể đẩy hộp nếu cần
        if self.can_move(x,y):
            current = self.worker()
            future = self.next(x,y)
            if current[2] == '@' and future == ' ':
                self.set_content(current[0]+x,current[1]+y,'@')
                self.set_content(current[0],current[1],' ')
                if save: self.stack.append((x,y,False))
            elif current[2] == '@' and future == '.':
                self.set_content(current[0]+x,current[1]+y,'+')
                self.set_content(current[0],current[1],' ')
                if save: self.stack.append((x,y,False))
            elif current[2] == '+' and future == ' ':
                self.set_content(current[0]+x,current[1]+y,'@')
                self.set_content(current[0],current[1],'.')
                if save: self.stack.append((x,y,False))
            elif current[2] == '+' and future == '.':
                self.set_content(current[0]+x,current[1]+y,'+')
                self.set_content(current[0],current[1],'.')
                if save: self.stack.append((x,y,False))
        elif self.can_push(x,y):
            current = self.worker()
            future = self.next(x,y)
            future_box = self.next(x+x,y+y)
            if current[2] == '@' and future == '$' and future_box == ' ':
                self.move_box(current[0]+x,current[1]+y,x,y)
                self.set_content(current[0],current[1],' ')
                self.set_content(current[0]+x,current[1]+y,'@')
                if save: self.stack.append((x,y,True))
            elif current[2] == '@' and future == '$' and future_box == '.':
                self.move_box(current[0]+x,current[1]+y,x,y)
                self.set_content(current[0],current[1],' ')
                self.set_content(current[0]+x,current[1]+y,'@')
                if save: self.stack.append((x,y,True))
            elif current[2] == '@' and future == '*' and future_box == ' ':
                self.move_box(current[0]+x,current[1]+y,x,y)
                self.set_content(current[0],current[1],' ')
                self.set_content(current[0]+x,current[1]+y,'+')
                if save: self.stack.append((x,y,True))
            elif current[2] == '@' and future == '*' and future_box == '.':
                self.move_box(current[0]+x,current[1]+y,x,y)
                self.set_content(current[0],current[1],' ')
                self.set_content(current[0]+x,current[1]+y,'+')
                if save: self.stack.append((x,y,True))
            elif current[2] == '+' and future == '$' and future_box == ' ':
                self.move_box(current[0]+x,current[1]+y,x,y)
                self.set_content(current[0],current[1],'.')
                self.set_content(current[0]+x,current[1]+y,'@')
                if save: self.stack.append((x,y,True))
            elif current[2] == '+' and future == '$' and future_box == '.':
                self.move_box(current[0]+x,current[1]+y,x,y)
                self.set_content(current[0],current[1],'.')
                self.set_content(current[0]+x,current[1]+y,'@')
                if save: self.stack.append((x,y,True))
            elif current[2] == '+' and future == '*' and future_box == ' ':
                self.move_box(current[0]+x,current[1]+y,x,y)
                self.set_content(current[0],current[1],'.')
                self.set_content(current[0]+x,current[1]+y,'+')
                if save: self.stack.append((x,y,True))
            elif current[2] == '+' and future == '*' and future_box == '.':
                self.move_box(current[0]+x,current[1]+y,x,y)
                self.set_content(current[0],current[1],'.')
                self.set_content(current[0]+x,current[1]+y,'+')
                if save: self.stack.append((x,y,True))

''' Tìm các bước di chuyển hợp lệ tiếp theo của một nút: công nhân có thể di chuyển vào một ô hoặc có thể đẩy một hộp'''
def validMove(state):
    x = 0
    y = 0
    move = []
    for step in ["U","D","L","R"]:
        if step == "U":
            x = 0
            y = -1
        elif step == "D":
            x = 0
            y = 1
        elif step == "L":
            x = -1
            y = 0
        elif step == "R":
            x = 1
            y = 0

        if state.can_move(x,y) or state.can_push(x,y):
            move.append(step)

    return move

def is_deadlock(state):
    box_list = state.box_list()
    for box in box_list:
        x = box[0]
        y = box[1]
        #corner up-left
        if state.get_content(x,y-1) in ['#','$','*'] and state.get_content(x-1,y) in ['#','$','*']:
            if state.get_content(x-1,y-1) in ['#','$','*']:
                return True
            if state.get_content(x,y-1) == '#' and state.get_content(x-1,y) =='#':
                return True
            if state.get_content(x,y-1) in ['$','*'] and state.get_content(x-1,y) in ['$','*']:
                if state.get_content(x+1,y-1) == '#' and state.get_content(x-1,y+1) == '#':
                    return True
            if state.get_content(x,y-1) in ['$','*'] and state.get_content(x-1,y) == '#':
                if state.get_content(x+1,y-1) == '#':
                    return True
            if state.get_content(x,y-1) == '#' and state.get_content(x-1,y) in ['$','*']:
                if state.get_content(x-1,y+1) == '#':
                    return True
                
        #corner up-right
        if state.get_content(x,y-1) in ['#','$','*'] and state.get_content(x+1,y) in ['#','$','*']:
            if state.get_content(x+1,y-1) in ['#','$','*']:
                return True
            if state.get_content(x,y-1) == '#' and state.get_content(x+1,y) =='#':
                return True
            if state.get_content(x,y-1) in ['$','*'] and state.get_content(x+1,y) in ['$','*']:
                if state.get_content(x-1,y-1) == '#' and state.get_content(x+1,y+1) == '#':
                    return True
            if state.get_content(x,y-1) in ['$','*'] and state.get_content(x+1,y) == '#':
                if state.get_content(x-1,y-1) == '#':
                    return True
            if state.get_content(x,y-1) == '#' and state.get_content(x+1,y) in ['$','*']:
                if state.get_content(x+1,y+1) == '#':
                    return True


        #corner down-left
        elif state.get_content(x,y+1) in ['#','$','*'] and state.get_content(x-1,y) in ['#','$','*']:
            if state.get_content(x-1,y+1) in ['#','$','*']:
                return True
            if state.get_content(x,y+1) == '#' and state.get_content(x-1,y) =='#':
                return True
            if state.get_content(x,y+1) in ['$','*'] and state.get_content(x-1,y) in ['$','*']:
                if state.get_content(x-1,y-1) == '#' and state.get_content(x+1,y+1) == '#':
                    return True
            if state.get_content(x,y+1) in ['$','*'] and state.get_content(x-1,y) == '#':
                if state.get_content(x+1,y+1) == '#':
                    return True
            if state.get_content(x,y+1) == '#' and state.get_content(x-1,y) in ['$','*']:
                if state.get_content(x-1,y-1) == '#':
                    return True
                

        #corner down-right
        elif state.get_content(x,y+1) in ['#','$','*'] and state.get_content(x+1,y) in ['#','$','*']:
            if state.get_content(x+1,y+1) in ['#','$','*']:
                return True
            if state.get_content(x,y+1) == '#' and state.get_content(x+1,y) =='#':
                return True
            if state.get_content(x,y+1) in ['$','*'] and state.get_content(x+1,y) in ['$','*']:
                if state.get_content(x-1,y+1) == '#' and state.get_content(x+1,y-1) == '#':
                    return True
            if state.get_content(x,y+1) in ['$','*'] and state.get_content(x+1,y) == '#':
                if state.get_content(x-1,y+1) == '#':
                    return True
            if state.get_content(x,y+1) == '#' and state.get_content(x+1,y) in ['$','*']:
                if state.get_content(x+1,y-1) == '#':
                    return True
           
    return False


def get_distance(state):
    sum = 0
    box_list = state.box_list()
    dock_list = state.dock_list()
    for box in box_list:
        for dock in dock_list:
            sum += (abs(dock[0] - box[0]) + abs(dock[1] - box[1]))
    return sum

def worker_to_box(state):
    p = 1000
    worker = state.worker()
    box_list = state.box_list()
    for box in box_list:
        if (abs(worker[0] - box[0]) + abs(worker[1] - box[1])) <= p:
            p = abs(worker[0] - box[0]) + abs(worker[1] - box[1])
    return p

def playByBot(game,move):
    if move == "U":
        game.move(0,-1,False)
    elif move == "D":
        game.move(0,1,False)
    elif move == "L":
        game.move(-1,0,False)
    elif move == "R":
        game.move(1,0,False)
    else:
        game.move(0,0,False)

def map_open(filename, level):
    matrix = []
    if int(level) < 1:
        print("LỖI: Cấp độ "+str(level)+" nằm ngoài phạm vi cho phép")
        sys.exit(1)
    else:
        file = open(filename,'r')
        level_found = False
        for line in file:
            row = []
            if not level_found:
                if  "Level "+str(level) == line.strip():
                    level_found = True
            else:
                if line.strip() != "":
                    row = []
                    for c in line:
                        if c != '\n' and c in [' ','#','@','+','$','*','.']:
                            row.append(c)
                        elif c == '\n': 
                            continue
                        else:
                            print("LỖI: Cấp độ "+str(level)+" có giá trị không hợp lệ "+c)
                            sys.exit(1)
                    matrix.append(row)
                else:
                    break
        return matrix

def print_game(matrix,screen):
    screen.blit(pygame.transform.scale(background, screen.get_size()), (0, 0))
    x = 0
    y = 0
    for row in matrix:
        for char in row:
            if char == ' ': 
                screen.blit(pygame.transform.scale(floor, (64, 64)),(x,y))
            elif char == '#': 
                screen.blit(pygame.transform.scale(wall, (64, 64)),(x,y))
            elif char == '@': 
                screen.blit(pygame.transform.scale(current_worker, (64, 64)),(x,y))
            elif char == '.': 
                screen.blit(pygame.transform.scale(docker, (64, 64)),(x,y))
            elif char == '*': 
                screen.blit(pygame.transform.scale(box_docked, (64, 64)),(x,y))
            elif char == '$': 
                screen.blit(pygame.transform.scale(box, (64, 64)),(x,y))
            elif char == '+': 
                screen.blit(pygame.transform.scale(current_worker, (64, 64)),(x,y))
            x = x + 64
        x = 0
        y = y + 64


def get_key():
  while 1:
    event = pygame.event.poll()
    if event.type == pygame.KEYDOWN:
      return event.key
    else:
      pass


def display_box(screen, message):
    """In một tin nhắn vào hộp ở giữa màn hình"""
    pygame.font.init()  # Khởi tạo hệ thống phông chữ
    try:
        fontobject = pygame.font.Font("ARIAL.TTF", 18)
    except:
        fontobject = pygame.font.SysFont(None, 18)
        
    pygame.draw.rect(screen, (0,0,0),
                    ((screen.get_width() / 2) - 100,
                     (screen.get_height() / 2) - 10,
                     200,20), 0)
    pygame.draw.rect(screen, (255,255,255),
                    ((screen.get_width() / 2) - 102,
                     (screen.get_height() / 2) - 12,
                     204,24), 1)
    if len(message) != 0:
        screen.blit(fontobject.render(message, 1, (255,255,255)),
                   ((screen.get_width() / 2) - 100, (screen.get_height() / 2) - 10))
    pygame.display.flip()

def display_end(screen, msg):
    pygame.font.init()  
    if msg == "Done":
        message = "Hoàn thành cấp độ"
    elif msg == "Cannot":
        message = "Không có giải pháp"
    elif msg == "Out":
        message = "Hết thời gian! Không tìm thấy giải pháp"
        
    try:
        fontobject = pygame.font.Font("ARIAL.TTF", 18)
    except:
        fontobject = pygame.font.SysFont(None, 18)
        
    pygame.draw.rect(screen, (0,0,0),
                    ((screen.get_width() / 2) - 100,
                     (screen.get_height() / 2) - 10,
                     200,20), 0)
    pygame.draw.rect(screen, (255,255,255),
                    ((screen.get_width() / 2) - 102,
                     (screen.get_height() / 2) - 12,
                     204,24), 1)
    screen.blit(fontobject.render(message, 1, (255,255,255)),
                ((screen.get_width() / 2) - 100, (screen.get_height() / 2) - 10))
    pygame.display.flip()

def ask(screen, question):
  "ask(screen, question) -> answer"
  pygame.font.init()
  current_string = []
  display_box(screen, question + ": " + "".join(current_string))
  while 1:
    inkey = get_key()
    if inkey == pygame.K_BACKSPACE:
      current_string = current_string[0:-1]
    elif inkey == pygame.K_RETURN:
      break
    elif inkey == pygame.K_MINUS:
      current_string.append("_")
    elif inkey <= 127:
      current_string.append(chr(inkey))
    display_box(screen, question + ": " + "".join(current_string))
  return "".join(current_string)

def create_start_screen():
    # Khởi tạo pygame
    pygame.init()
    
    # Thiết lập cửa sổ game
    WINDOW_SIZE = (800, 600)
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Sokoban Game")

    # Màu sắc
    WHITE = (255, 255, 255)
    DARK_GREEN = (100, 167, 0)

    # Font cho text
    font = pygame.font.Font("ARIAL.TTF", 100)
    small_font = pygame.font.Font("ARIAL.TTF", 24)
    very_small_font = pygame.font.Font("ARIAL.TTF",20)

    # Input box
    input_box = pygame.Rect(WINDOW_SIZE[0]//2 - 100, WINDOW_SIZE[1]//2 + 50, 200, 50)
    input_text = ""
    input_active = False
    
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    input_active = True
                else:
                    input_active = False
                    
            if event.type == KEYDOWN:
                if input_active:
                    if event.key == K_RETURN:
                        if input_text.isdigit() and int(input_text) > 0:
                            pygame.quit()
                            return input_text
                        else:
                            input_text = ""
                    elif event.key == K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.unicode.isdigit():  # Chỉ cho phép nhập số
                        input_text += event.unicode
                        
        # Vẽ background
        screen.fill(DARK_GREEN)

        # Vẽ logo
        title_text = font.render("SOKOBAN", True, WHITE)
        title_rect = title_text.get_rect(center=(WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//2.8))
        screen.blit(title_text, title_rect)
            
        # Vẽ label cho input box
        label = small_font.render("Nhập cấp độ:", True, WHITE)
        label_rect = label.get_rect(center=(WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//1.8))
        screen.blit(label, label_rect)
        
      # Vẽ input box
        pygame.draw.rect(screen, WHITE, input_box, 2)
        text_surface = small_font.render(input_text, True, WHITE)
        text_rect = text_surface.get_rect(center=input_box.center)
        screen.blit(text_surface, text_rect)

        # Hiển thị hướng dẫn với khoảng cách
        hint_text = small_font.render("Nhấn Enter để bắt đầu", True, WHITE)
        hint_rect = hint_text.get_rect(center=(WINDOW_SIZE[0]//2, WINDOW_SIZE[1]//2 + 130))  
        screen.blit(hint_text, hint_rect)


        # Thêm hướng dẫn phím điều khiển
        controls = [
            "Mũi tên ↑ ↓ ← →: Di chuyển | D: Hoàn tác bước di chuyển | N: Cấp độ tiếp theo",
            "M: Cấp độ trước | Q: Thoát trò chơi | A: Giải thuật Astar  B: Giải thuật BFS",
            "Q: Thoát trò chơi",
        ]

        y_offset = WINDOW_SIZE[1]//2 + 160
        for line in controls:
            control_text = very_small_font.render(line, True, WHITE)
            control_rect = control_text.get_rect(center=(WINDOW_SIZE[0]//2, y_offset))
            screen.blit(control_text, control_rect)
            y_offset += 30  # Tăng khoảng cách giữa các dòng hướng dẫn

        pygame.display.flip()


def start_game():
    level = create_start_screen()
    if int(level) > 0:
        return level
    else:
        print("LỖI: Cấp độ không hợp lệ: " + str(level))
        sys.exit(2)

# Tải các hình cho các hướng khác nhau của người chơi
worker_up = pygame.image.load('image/Player_up.png')
worker_down = pygame.image.load('image/Player_down.png') 
worker_left = pygame.image.load('image/Player_left.png')
worker_right = pygame.image.load('image/Player_right.png')

wall = pygame.image.load('image/wall2.png')
floor = pygame.image.load('image/grass1.png')
box = pygame.image.load('image/CrateDark_Brown.png')
box_docked = pygame.image.load('image/Crate_Yellow.png')
docker = pygame.image.load('image/EndPoint_Yellow.png')
background = pygame.image.load('image/grass1.png')

# Đầu tiên, thêm các hàm này trước vòng lặp trò chơi chính:

def load_new_level(level):
    try:
        game = Game(map_open('.\levels', level))
        return game, game.load_size()
    except:
        print(f"LỖI: Không thể tải cấp độ {level}")
        return None, None

def reset_game_state():
    global sol, i, flagAuto
    sol = ""
    i = 0 
    flagAuto = 0


class AI:
    def AstarSolution(game):
        start = time.time()
        node_generated = 0
        state = copy.deepcopy(game) 
        state.heuristc = worker_to_box(state) + get_distance(state)
        node_generated += 1
        
        if is_deadlock(state):
            end = time.time()
            print("Thời gian tìm giải pháp:",round(end -start,2))
            print("Số node đã thăm:",node_generated)
            print("Không có giải pháp!")
            return "NoSol"                 
        
        stateSet = queue.PriorityQueue() 
        stateSet.put(state)
        stateExplored = []
        print("Đang xử lý...")
        
        while not stateSet.empty():
            if (time.time() - start) >= TIME_LIMITED:
                print("Hết thời gian!")
                return "TimeOut"         
                          
            currState = stateSet.get() 
            move = validMove(currState)
            stateExplored.append(currState.get_matrix()) 
                    
            for step in move:                              
                newState = copy.deepcopy(currState)
                node_generated += 1
                if step == "U":
                    newState.move(0,-1,False)
                elif step == "D":
                    newState.move(0,1,False)
                elif step == "L":
                    newState.move(-1,0,False)
                elif step == "R":
                    newState.move(1,0,False)
                    
                newState.pathSol += step
                newState.heuristic = worker_to_box(newState) + get_distance(newState)
            
                if newState.is_completed():
                    end = time.time()
                    print("Thời gian tìm giải pháp:",round(end -start,2),"giây")
                    print("Số node đã thăm:",node_generated)
                    print("Giải pháp:",newState.pathSol)
                    return newState.pathSol

            
                if (newState.get_matrix() not in stateExplored) and (not is_deadlock(newState)):
                    stateSet.put(newState)
                    
        end = time.time()
        print("Thời gian tìm giải pháp:",round(end -start,2))
        print("Số node đã thăm:",node_generated)
        print("Không có giải pháp!")
        return "NoSol"


if __name__ == "__main__":  
    current_worker = worker_down
    pygame.init()

    level = start_game()
    current_level = int(level)
    game = Game(map_open('.\levels',current_level))
    size = game.load_size()
    screen = pygame.display.set_mode(size)
    sol = ""
    i = 0
    flagAuto = 0

    while 1:
        print_game(game.get_matrix(),screen)

        if sol == "NoSol":
            display_end(screen,"Cannot")
        if sol == "TimeOut":
            display_end(screen,"Out")
        if game.is_completed():
            display_end(screen,"Done")

        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_n:  # Next level
                    current_level += 1
                    new_game, new_size = load_new_level(current_level)
                    if new_game:
                        game = new_game
                        if new_size != size:
                            size = new_size
                            screen = pygame.display.set_mode(size)
                        reset_game_state()
                    else:
                        current_level -= 1
                elif event.key == pygame.K_m:  # Previous level
                    if current_level > 1:
                        current_level -= 1
                        new_game, new_size = load_new_level(current_level)
                        if new_game:
                            game = new_game
                            if new_size != size:
                                size = new_size
                                screen = pygame.display.set_mode(size)
                            reset_game_state()
                        else:
                            current_level += 1
                elif event.key == pygame.K_a:
                    sol = AI.AstarSolution(game)
                    flagAuto = 1
                elif event.key == pygame.K_b:
                    sol = AI.BFSsolution(game)
                    flagAuto = 1
                elif event.key == pygame.K_UP: 
                    current_worker = worker_up
                    game.move(0,-1, True)
                elif event.key == pygame.K_DOWN:
                    current_worker = worker_down 
                    game.move(0,1, True)
                elif event.key == pygame.K_LEFT:
                    current_worker = worker_left
                    game.move(-1,0, True)
                elif event.key == pygame.K_RIGHT:
                    current_worker = worker_right
                    game.move(1,0, True)
                elif event.key == pygame.K_q: sys.exit(0)
                elif event.key == pygame.K_d: game.unmove()
                elif event.key == pygame.K_c: sol = ""

        if (flagAuto) and (i < len(sol)):
            # Cập nhật hình ảnh người chơi khi tự động di chuyển
            if sol[i] == 'U':
                current_worker = worker_up
            elif sol[i] == 'D':
                current_worker = worker_down
            elif sol[i] == 'L':
                current_worker = worker_left
            elif sol[i] == 'R':
                current_worker = worker_right
                
            playByBot(game,sol[i])
            i += 1
            if i == len(sol): flagAuto = 0
            time.sleep(0.1)

        pygame.display.update()
