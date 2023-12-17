import sys
import time
import random
import pygame
from collections import deque
import cv2 as cv
import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_face_mesh = mp.solutions.face_mesh

pygame.init()

VID_CAP = cv.VideoCapture(0)
window_size = (int(VID_CAP.get(cv.CAP_PROP_FRAME_WIDTH)), int(VID_CAP.get(cv.CAP_PROP_FRAME_HEIGHT)))
screen = pygame.display.set_mode(window_size)

# Santa and pipe initialization
santa_img = pygame.image.load("santa1.png")
santa_img = pygame.transform.scale(santa_img, (santa_img.get_width() // 6, santa_img.get_height() // 6))
santa_frame = santa_img.get_rect(center=(window_size[0] // 6, window_size[1] // 2))

pipe_frames = deque()
pipe_img = pygame.image.load("giftscol.png")
pipe_starting_template = pipe_img.get_rect()
space_between_pipes = 300

game_clock = time.time()
pipe_spawn_timer = 0
time_between_pipe_spawn = 40
dist_between_pipes = 550

# Difficulty levels
difficulty_levels = {
    "1": 0.8,
    "2": 1.0,
    "3": 1.2,
}

selected_difficulty = None

while selected_difficulty not in difficulty_levels:
    selected_difficulty = input("Select difficulty (1/2/3): ").lower()

pipe_velocity_multiplier = difficulty_levels[selected_difficulty]

score = 0
did_update_score = False
game_is_running = True
game_over = False

# Initialize Face Mesh
with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as face_mesh:
    while True:
        if game_over:
            text = pygame.font.SysFont("Helvetica Bold.ttf", 64).render('Game over!', True, (99, 245, 255))
            tr = text.get_rect(center=(window_size[0] / 2, window_size[1] / 2))
            screen.blit(text, tr)
            restart_text = pygame.font.SysFont("Helvetica Bold.ttf", 36).render('Press "R" to restart', True, (255, 255, 255))
            restart_rect = restart_text.get_rect(center=(window_size[0] / 2, window_size[1] / 2 + 50))
            screen.blit(restart_text, restart_rect)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        game_over = False
                        score = 0
                        santa_frame.centery = window_size[1] // 2
                        pipe_frames.clear()
                        pipe_spawn_timer = 0
                        game_clock = time.time()

            continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                VID_CAP.release()
                cv.destroyAllWindows()
                pygame.quit()
                sys.exit()

        ret, frame = VID_CAP.read()
        if not ret:
            print("Empty frame, continuing...")
            continue

        screen.fill((125, 220, 232))

        frame.flags.writeable = False
        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = face_mesh.process(frame)
        frame.flags.writeable = True

        if results.multi_face_landmarks and len(results.multi_face_landmarks) > 0:
            marker = results.multi_face_landmarks[0].landmark[94].y
            santa_frame.centery = (marker - 0.5) * 1.5 * window_size[1] + window_size[1] / 2
            santa_frame.y = max(0, min(santa_frame.y, window_size[1] - santa_frame.height))

        frame = cv.flip(frame, 1).swapaxes(0, 1)

        pipe_velocity = dist_between_pipes / (time_between_pipe_spawn * pipe_velocity_multiplier)

        for pf in pipe_frames:
            pf[0].x -= pipe_velocity
            pf[1].x -= pipe_velocity

        if len(pipe_frames) > 0 and pipe_frames[0][0].right < 0:
            pipe_frames.popleft()

        pygame.surfarray.blit_array(screen, frame)
        screen.blit(santa_img, santa_frame)
        checker = True
        for pf in pipe_frames:
            if pf[0].left <= santa_frame.x <= pf[0].right:
                checker = False
                if not did_update_score:
                    score += 1
                    did_update_score = True
            screen.blit(pipe_img, pf[1])
            screen.blit(pygame.transform.flip(pipe_img, 0, 1), pf[0])
        if checker:
            did_update_score = False

        text = pygame.font.SysFont("Helvetica Bold.ttf", 50).render(f'Difficulty: {selected_difficulty.capitalize()}', True, (255, 0, 0))
        tr = text.get_rect(center=(100, 50))
        screen.blit(text, tr)
        text = pygame.font.SysFont("Helvetica Bold.ttf", 50).render(f'Score: {score}', True, (255, 0, 0))
        tr = text.get_rect(center=(100, 100))
        screen.blit(text, tr)

        pygame.display.flip()

        if any([santa_frame.colliderect(pf[0]) or santa_frame.colliderect(pf[1]) for pf in pipe_frames]):
            game_over = True

        if pipe_spawn_timer == 0:
            top = pipe_starting_template.copy()
            top.x, top.y = window_size[0], random.randint(120 - 1000, window_size[1] - 120 - space_between_pipes - 1000)
            bottom = pipe_starting_template.copy()
            bottom.x, bottom.y = window_size[0], top.y + 1000 + space_between_pipes
            pipe_frames.append([top, bottom])

        pipe_spawn_timer += 1
        if pipe_spawn_timer >= time_between_pipe_spawn:
            pipe_spawn_timer = 0
