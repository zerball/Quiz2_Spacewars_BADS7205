#!/usr/bin/env python3
"""
Game name:		Space Wars (change to cooler name)
Author:			Dan Petersson
Github link:	https://github.com/DanPetersson/SpaceWars

Description:
---------------------------------------------------------
- Survive as long as possible as shoot as many aliens as possible to get good score

---------------------------------------------------------
Python:			3.8 						
PyGame:			1.9.6

Revision updates:
---------------------------------------------------------
Backlog_revision_history.txt

"""
import pickle
import river
import pygame
import random
import math
import os
import json
import time
import sqlite3
import threading
import statistics
from datetime import datetime
from high_scores import high_scores
import logging
import time
import joblib
#import space_wars_settings as sws

# ------------------
# Netpie
# ------------------

import microgear.client as microgear
import logging
import time

score_list = []
publish_time = datetime.now()

appid = 'datastream'
gearkey = 'qY0dhxc3TAswzeC'
gearsecret = 'eNInuhdaicInPOJl0KfPrBJfS'
user_score_topic = '/user_score_topic'

microgear.create(gearkey, gearsecret, appid, {'debugmode': True})
microgear.setalias("tanapong")

def connection():
    logging.info("Now I am connected with netpie")

def subscription(topic, message):
	import ast
	global score_list

	try:
		if topic == f"/{appid}{user_score_topic}" and message:
			score = json.loads(ast.literal_eval(message).decode('utf-8'))
			score_list.append(score)
	except Exception:
		pass
	logging.info(topic + " " + message)

def disconnect():
    logging.info("disconnected")

microgear.on_connect = connection
microgear.on_message = subscription
microgear.on_disconnect = disconnect
microgear.subscribe(user_score_topic)
microgear.connect(False)

### Analytic Model
dt_scaler = joblib.load('./model/scaler.bin')
decision_tree = joblib.load('./model/model.h5')
LABELS = {2: 'Hardcore Achiever', 3: 'Hardcore Killer', 1: 'Casual Achiever', 0: 'Casual Killer'}
labels_new = {2: 'Hardcore Achiever', 0: 'Hardcore Killer', 1: 'Casual Achiever', 3: 'Casual Killer'}

classes = []
model_new = joblib.load('model2.h5')

def prediction_user_type(level, keyX_pressed_count, keyY_pressed_count, respawn_enemy_count, respawn_coin_count):
	global A0, A1
	a0 = statistics.mean(A0) if len(A0) else 0
	a1 = statistics.mean(A1) if len(A1) else 0
	a2 = coin_count
	a3 = destroyed_enemy_count
	a4 = shots_count
	a5 = A4 - A3
	a6 = level
	a7 = keyX_pressed_count
	a8 = keyY_pressed_count
	a9 = respawn_enemy_count
	a10 = respawn_coin_count
	# a11 = a3/a9
	# a12 = a2/a10
	X = [[a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10]]

	X_scale = dt_scaler.transform(X)
	y = decision_tree.predict(X_scale)[0]
	return LABELS.get(y)

def new_prediction_user_type(level, keyX_pressed_count, keyY_pressed_count, respawn_enemy_count, respawn_coin_count):
	global A0, A1
	a0 = statistics.mean(A0) if len(A0) else 0
	a1 = statistics.mean(A1) if len(A1) else 0
	a2 = coin_count
	a3 = destroyed_enemy_count
	a4 = shots_count
	a5 = A4 - A3
	a6 = level
	a7 = keyX_pressed_count
	a8 = keyY_pressed_count
	a9 = respawn_enemy_count
	a10 = respawn_coin_count
	# a11 = a3/a9
	# a12 = a2/a10
	X = {2:a2, 3:a3, 4:a4, 6:a6, 7:a7, 8:a8, 9:a9, 10:a10}

	y = model_new.predict_one(X)
	classes.append(labels_new.get(y))
	# print(y)
	return labels_new.get(y)



# initialize pygame 
pygame.init()

# Initialize global fonts
font_huge	= pygame.font.Font('freesansbold.ttf', 128)
font_large	= pygame.font.Font('freesansbold.ttf', 64)
font_medium	= pygame.font.Font('freesansbold.ttf', 32)
font_small	= pygame.font.Font('freesansbold.ttf', 16)
font_tiny	= pygame.font.Font('freesansbold.ttf', 8)

# Initialize global Game Colors
black 			= (  0,   0,   0)
white 			= (255, 255, 255)

red 			= (200,   0,   0)
green 			= (  0, 200,   0)
blue 			= (  0,   0, 200)
yellow 			= (200, 200,   0)

light_red 		= (255,   0,   0)
Light_green 	= (  0, 255,   0)
light_blue 		= (  0,   0, 255)
light_yellow	= (255, 255,   0)


# ----------------------------
# 		Define Classes
# ----------------------------

class SpaceObject:

	def __init__(self, image, explosion_image, posX=0, posY=0, speedX = 0, speedY = 0, sizeX = 64, sizeY = 64, 
					state = 'show', sound = ' ', hit_points = 1):
		#self.namme	= name
		self.image  = image
		self.explosion_image = explosion_image 
		self.sizeX  = sizeX
		self.sizeY  = sizeY
		self.posX   = posX
		self.posY   = posY
		self.speedX = speedX
		self.speedY	= speedY
		self.state	= state		# 'hide', 'show'
		self.sound 	= sound
		self.explosion_counter = -1
		self.hit_points = hit_points

	def show(self):
		if self.state == 'show' and self.explosion_counter <= 0:
			screen.blit(self.image, (int(self.posX), int(self.posY)))
		elif self.explosion_counter > 0:
			screen.blit(self.explosion_image, (int(self.posX), int(self.posY)))
			
class SpaceShip(SpaceObject):
    
    # def __init__(self):
    #     super().__init__()

	def update_player_postion(self, screen_sizeX, screen_sizeY):

		# Update X position (update with min/max)
		self.posX += self.speedX
		if self.posX < 0:
			self.posX = 0
		elif self.posX > screen_sizeX-self.sizeX:
			self.posX = screen_sizeX-self.sizeX

		# Update Y position (update with min/max)
		self.posY += self.speedY
		if self.posY < 0:
			self.posY = 0
		elif self.posY > screen_sizeY-self.sizeY:
			self.posY = screen_sizeY-self.sizeY


class SpaceEnemy(SpaceObject):

	def update_enemy_position(self, screen_sizeX, screen_sizeY):

		# Update X position
		self.posX += self.speedX

		# Update Y position
		self.posY += self.speedY


class SpaceCoin(SpaceObject):

	def update_coin_position(self, screen_sizeX, screen_sizeY):

		# Update X position
		self.posX += self.speedX

		# Update Y position
		self.posY += self.speedY


class Bullet(SpaceObject):

	def update_bullet_position(self, screen_sizeX, screen_sizeY):

		# Update X position
		self.posX += self.speedX

		# Update Y position, and change state if outside screen
		self.posY += self.speedY
		if self.posY < -self.sizeY:
			self.state = 'hide'


	def fire_bullet(self, player):

		self.posX = player.posX + player.sizeX/2 - self.sizeX/2
		self.posY = player.posY
		self.sound.play()
		self.state = 'show'


class Button:

	def __init__(self, centerX, centerY, width, hight, text='', color=yellow, color_hoover=light_yellow, 
		text_color=black, text_hoover=black, font=font_small):
		self.centerX 		= int(centerX)
		self.centerY		= int(centerY)
		self.width 			= int(width)
		self.hight 			= int(hight)
		self.X				= int(centerX - width/2)
		self.Y				= int(centerY - hight/2)

		self.text 			= text
		self.color 			= color
		self.color_hoover	= color_hoover
		self.text_color		= text_color
		self.text_hoover	= text_hoover
		self.font 			= font
		self.clicked		= False

	# internal only function ?
	def text_objects(text, font, color):
	    text_surface = font.render(text, True, color)
	    return text_surface, text_surface.get_rect()

	# internal only function ?
	def message_display_center(text, font, color, centerX, centerY):
	    text_surface, text_rectangle = text_objects(text, font, color)
	    text_rectangle.center = (centerX,centerY)
	    screen.blit(text_surface, text_rectangle)

	def show(self, mouse=(0,0)):
		if self.X < mouse[0] < self.X + self.width and self.Y < mouse[1] < self.Y + self.hight:
			pygame.draw.rect(screen, self.color_hoover, (self.X, self.Y, self.width, self.hight))
		else:
			pygame.draw.rect(screen, yellow, (self.X, self.Y, self.width, self.hight))
		message_display_center(self.text, self.font, black, self.centerX, self.centerY)

	def check_clicked(self, mouse, mouse_click):
		if self.X < mouse[0] < self.X + self.width and self.Y < mouse[1] < self.Y + self.hight and mouse_click[0] == 1:
			self.clicked = True
		else:
			self.clicked = False



# ----------------------------
# 		Define Procedures
# ----------------------------


def text_objects(text, font, color):
	# Mainly supporting for function message_dipslay
    text_surface = font.render(text, True, color)
    return text_surface, text_surface.get_rect()

def message_display_center(text, font, color, centerX, centerY):
    text_surface, text_rectangle = text_objects(text, font, color)
    text_rectangle.center = (centerX,centerY)
    screen.blit(text_surface, text_rectangle)

def message_display_left(text, font, color, leftX, centerY):
    text_surface, text_rectangle = text_objects(text, font, color)
    text_rectangle.midleft = (leftX, centerY)
    screen.blit(text_surface, text_rectangle)

def message_display_right(text, font, color, rightX, centerY):
    text_surface, text_rectangle = text_objects(text, font, color)
    text_rectangle.midright = (rightX, centerY)
    screen.blit(text_surface, text_rectangle)

def show_high_scores():

#	global db_connection

	high_scores_screen = True
	while high_scores_screen:

		screen.fill(background_color)
		screen.blit(background_image[0], (0,0))

		message_display_center('High Scores', font_large, yellow, int(screen_sizeX/2), int(screen_sizeY * 1/10))
		message_display_center('Press (D)elete or any other key to continue', font_medium, yellow, int(screen_sizeX/2), int(screen_sizeY *9/10))

		top_5 = high_scores.high_scores_top_list(db_connection)

		index = 0
		for entry in top_5:
			# timestamp, name, score, date
			index += 1
			message_display_left(str(entry[1]), font_medium, yellow, int(screen_sizeX * 1/8), int(screen_sizeY *(2+index)/10))
			message_display_right(str(entry[2]), font_medium, yellow, int(screen_sizeX * 2/4), int(screen_sizeY *(2+index)/10))
			message_display_center(str(entry[3]), font_medium, yellow, int(screen_sizeX * 3/4), int(screen_sizeY *(2+index)/10))


		for event in pygame.event.get():	
			if event.type == pygame.QUIT:
				# add even mouse click ?
				high_scores_screen = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_d:
					# Deletes high score db table and recreates empty one
					high_scores.high_scores_db_delete(db_connection)
					high_scores.high_scores_create_table(db_connection)
				else:
					high_scores_screen = False

		# Display intro screen
		pygame.display.update()


def menu():
	# into screen 
	
	intro_screen = True
	while intro_screen:

		screen.fill(background_color)
		screen.blit(background_image[0], (0,0))

		message_display_center('SPACE WARS', font_large, yellow, int(screen_sizeX/2), int(screen_sizeY/3))
		message_display_center('New Game (Y/N)', font_medium, yellow, int(screen_sizeX/2), int(screen_sizeY *3/5))

		# get mouse position
		mouse = pygame.mouse.get_pos()
		mouse_click = pygame.mouse.get_pressed()

		# Define and draw buttons
		button_width 	= 130
		button_hight 	= 50

		# Define and draw "Yes" button
		yes_button_X 	= int(screen_sizeX*1/4)
		yes_button_Y 	= 450
		yes_button 		= Button(yes_button_X, yes_button_Y, button_width, button_hight, 'Yes')
		yes_button.show(mouse)
		yes_button.check_clicked(mouse, mouse_click)

		# Define and draw "No" button
		no_button_X 	= int(screen_sizeX*2/4)
		no_button_Y 	= yes_button_Y
		no_button  		= Button(no_button_X,  no_button_Y,  button_width, button_hight, 'No')
		no_button.show(mouse)
		no_button.check_clicked(mouse, mouse_click)

		# Define and draw "High Scores" (hs) button
		hs_button_X 	= int(screen_sizeX*3/4)
		hs_button_Y 	= yes_button_Y
		hs_button  		= Button(hs_button_X,  hs_button_Y,  button_width, button_hight, 'High Scores')
		hs_button.show(mouse)
		hs_button.check_clicked(mouse, mouse_click)

		if yes_button.clicked:
			intro_screen = False
			quit_game = False
		if no_button.clicked:
			intro_screen = False
			quit_game = True

		if hs_button.clicked:
			show_high_scores()

		for event in pygame.event.get():	
			if event.type == pygame.QUIT:
				intro_screen = False
				quit_game = True

		# if 'Y' or 'N' key is pressed
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_y or event.key == pygame.K_z or event.key == pygame.K_RETURN:
					intro_screen = False
					quit_game = False
				if event.key == pygame.K_n:
					intro_screen = False
					quit_game = True

		# Display intro screen
		pygame.display.update()

	return quit_game

def paused(screen_sizeX, screen_sizeY):

	largeText = pygame.font.SysFont("freesansbold",115)
	TextSurf, TextRect = text_objects("Paused", largeText)
	TextRect.center = ((screen_sizeX/2),(screen_sizeX/2))
	screen.blit(TextSurf, TextRect)

	pause = True
	while pause:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				quit()
			if event.type == pygame.KEYDOWN:
				# 'p' for unpause 
				if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
					pause = False
		screen.blit(TextSurf, TextRect)
		pygame.display.update()

		

def respawn(enemy, level):
	enemy.explosion_counter = -1	
	enemy.posX 	= random.randint(0, screen_sizeX - enemy.sizeX) 
	enemy.posY 	= random.randint(-screen_sizeY, -100)
	if enemy.posX < screen_sizeX / 3:
		enemy.speedX = random.randint(0, 10) / 10 * enemy.speedY
	elif enemy.posX > screen_sizeX * 2 / 3:
		enemy.speedX = random.randint(-10, 0) / 10 * enemy.speedY
	else:
		enemy.speedX = random.randint(-5, 5) / 10 * enemy.speedY
	
#	enemy.speedY = level
	
def is_collision(object1, object2):

	obj1_midX = object1.posX + object1.sizeX
	obj1_midY = object1.posY + object1.sizeY
	obj2_midX = object2.posX + object2.sizeX
	obj2_midY = object2.posY + object2.sizeY

	# think if I want to improve this...
	distance = math.sqrt(math.pow(obj1_midX-obj2_midX,2) + math.pow(obj1_midY-obj2_midY,2))
	collision_limit = (object1.sizeX + object1.sizeY + object2.sizeX + object2.sizeY) / 5

	return distance < collision_limit

def show_explosion(object, image):
	screen.blit(image, (int(object.posX), int(object.posY)))


def show_online_score(font_size = 16, x=100, y=10):
	global score_list
	score_font = pygame.font.Font('freesansbold.ttf', font_size)

	sorted_user_scores = sorted(score_list, key=lambda x: x['score'], reverse=True)
	
	top_rank = []
	for user_score in sorted_user_scores:
		user_exists = next(filter(lambda x: x['user'] == user_score['user'], top_rank), None)
		if not user_exists:
			top_rank.append(user_score)

	y_pos = y
	for user_score in top_rank:
		name_text = score_font.render(f"{user_score['user']}: {user_score['score']}", True, (255, 255, 0))
		screen.blit(name_text, (screen_sizeX - x, y_pos))
		y_pos = y_pos + 5 + font_size


def show_score(score, level, name, coin_count, font_size = 16, x=10, y=10, game_over=False, user_type=None, new_user_type=None):
	score_font = pygame.font.Font('freesansbold.ttf', font_size)
	level_text = score_font.render("Level  : " + str(level), True, (255, 255, 0))
	score_text = score_font.render("Score : " + str(score), True, (255, 255, 0))
	name_text = score_font.render("Name : " + str(name), True, (255, 255, 0))
	coin_text = score_font.render("Coin : " + str(coin_count), True, (255, 255, 0))
	if user_type:
		user_type_text = score_font.render("You are : " + str(user_type), True, (255, 255, 0))
	if new_user_type:
		new_user_type_text = score_font.render("NEW! You are : " + str(new_user_type), True, (255, 0, 0))

	y_pos = y
	screen.blit(level_text, (x, y_pos))
	y_pos = y_pos + 5 + font_size
	screen.blit(score_text, (x, y_pos))
	y_pos = y_pos + 5 + font_size
	screen.blit(name_text, (x, y_pos))
	y_pos = y_pos + 5 + font_size
	screen.blit(coin_text, (x, y_pos))

	if user_type:
		y_pos = y_pos + 5 + font_size
		screen.blit(user_type_text, (x, y_pos))
	
	if new_user_type:
		y_pos = y_pos + 5 + font_size
		screen.blit(new_user_type_text, (x, y_pos))

	publish_online_score(score, name, game_over)


def publish_online_score(score, name, game_over):
	global publish_time, microgear
	sending_interval = 0.5
	now = datetime.now()
	if (now - publish_time).seconds >= sending_interval:
		data = dict(user=name, score=score)
		microgear.publish(user_score_topic, json.dumps(data))
		publish_time = now

 
def show_game_over(screen_sizeX, screen_sizeY, score, high_score, coin_count, user_type):
	
	# Move enemies below screen (is there a better way?)
	for i in range(num_of_enemies):
		enemy[i].posY = screen_sizeY + 100

	# Display text and score
	message_display_center('GAME OVER', font_large, yellow, int(screen_sizeX/2), int(screen_sizeY * 3/20))
	message_display_center('You\'re a', font_medium, yellow, int(screen_sizeX/2), int(screen_sizeY * 3/10))
	message_display_center('NEW! You\'re a ' + max(set(classes), key = classes.count), font_medium, yellow, int(screen_sizeX/2), int(screen_sizeY * 4/10))
	message_display_center(user_type, font_medium, yellow, int(screen_sizeX/2), int(screen_sizeY * 5/10))
	message_display_center('Score: ' + str(score), font_medium, yellow, int(screen_sizeX/2), int(screen_sizeY *6/10))
	message_display_center('Coins: ' + str(coin_count), font_medium, yellow, int(screen_sizeX/2), int(screen_sizeY *7/10))
	message_display_center('Highscore: ' + str(high_score), font_medium, yellow, int(screen_sizeX/2), int(screen_sizeY *8/10))
	message_display_center('Press any key to continue', font_medium, yellow, int(screen_sizeX/2), int(screen_sizeY *9/10))


#############################
#		Main Program		#
#############################
#if __name__ == '__main__':

# # initialize pygame 
# pygame.init()

# # Initialize fonts
# font_huge	= pygame.font.Font('freesansbold.ttf', 128)
# font_large	= pygame.font.Font('freesansbold.ttf', 64)
# font_medium	= pygame.font.Font('freesansbold.ttf', 32)
# font_small	= pygame.font.Font('freesansbold.ttf', 16)
# font_tiny	= pygame.font.Font('freesansbold.ttf', 8)


# Initialize Global CONSTANTS from space_wars_settings.py (sws)
MUSIC 		= False 		#sws.MUSIC 		# True
GAME_SPEED 	= 5 		#sws.GAME_SPEED 	# 1 to 5
PLAYER_NAME	= 'InwZa'		#sws.PLAYER_NAME	# 'DAN'


# Initialize Global variables
screen_sizeX = 800
screen_sizeY = 600
screen_size = (screen_sizeX, screen_sizeY)
background_color = black
# Initialize screen
screen = pygame.display.set_mode((screen_sizeX, screen_sizeY))
# screen = pygame.display.set_mode((screen_sizeX, screen_sizeY), flags=pygame.FULLSCREEN)


# Get working directory and subdirectories
dir_path = os.getcwd()
images_path = os.path.join(dir_path, 'images')
sounds_path = os.path.join(dir_path, 'sounds')


# Initialize images
icon_image			= pygame.image.load(os.path.join(images_path , 'icon_07.png'))
player_image		= pygame.image.load(os.path.join(images_path, 'MilFal_03.png'))
bullet_image		= pygame.image.load(os.path.join(images_path, 'bullet.png'))
enemy_image	    	= [pygame.image.load(os.path.join(images_path, 'ufo_01.png')),
				       pygame.image.load(os.path.join(images_path, 'ufo_02.png')),
				       pygame.image.load(os.path.join(images_path, 'ufo_03.png')),
				       pygame.image.load(os.path.join(images_path, 'ufo_04.png')),
				       pygame.image.load(os.path.join(images_path, 'spaceship_03_usd.png')),
				       pygame.image.load(os.path.join(images_path, 'spaceship_01_usd.png')),
					   pygame.image.load(os.path.join(images_path, 'death_star_02.png')),
					   pygame.image.load(os.path.join(images_path, 'death_star_03.png'))]
coin_image			= pygame.image.load(os.path.join(images_path, 'coin.png'))
explosion_image		= [pygame.image.load(os.path.join(images_path, 'explosion_01.png')),
				       pygame.image.load(os.path.join(images_path, 'explosion_02.png'))]
background_image	= [pygame.image.load(os.path.join(images_path, 'background_03.jpg')), 
					   pygame.image.load(os.path.join(images_path, 'background_03_usd.jpg'))]
background_image_hight = 600
				      
# Caption and Icon
pygame.display.set_caption("Space Wars")
pygame.display.set_icon(icon_image)

# Initialize sounds
bullet_sound		= pygame.mixer.Sound(os.path.join(sounds_path, 'laser.wav'))
explosion_sound		= pygame.mixer.Sound(os.path.join(sounds_path, 'explosion.wav'))

# Start backgound music
if MUSIC:
	pygame.mixer.music.load(os.path.join(sounds_path, 'background.wav'))
	pygame.mixer.music.play(-1)

# Initialize game speed settings
frames_per_second = 20 + 10 * GAME_SPEED
clock = pygame.time.Clock()

# Initialize connection to high score database
db_connection = high_scores.high_scores_connect_to_db('high_scores.db')
high_scores.high_scores_create_table(db_connection)

# Initialize settings
player_maxSpeedX	= 3.5			# recommended: 3
player_maxSpeedY	= 3.5			# recommended: 3
enemy_maxSpeedX		= 2
enemy_maxSpeedY		= 2
bullet_speed		= 10

session_high_score 	= 0

# Initialize collection data
thread = None
A0 = [] # A0) Position in X axis => position X [1, 2, 3, 2, 1] / 5
A1 = [] # A1) Position in Y axis => position Y [200, 150, 130, 170] / 4
A2 = 0  # A2) Number of coins collected => Total
A3 = 0  # A3) Number of destroyed enemies => Total
A4 = 0  # A4) Number of shots => Total
A5 = 0  # A5) Number of shots without enemies => Total (A4 - A3)
A6 = 0  # A6) Level reach
A7 = 0  # A7) key X pressed count
A8 = 0  # A8) key Y pressed count
A9 = 0  # A9) Number of enemy created
A10 = 0  # A10) Number of coin created


def thread_collect_data():
    global thread, A0, A1, A2, A3, A4, A5, player
    if not go_to_menu and not quit_game:
	    A0 += [player.posX]
	    A1 += [player.posY]
	    thread = threading.Timer(1, thread_collect_data)
	    thread.start()

def save_collection_data(level, keyX_pressed_count, keyY_pressed_count, respawn_enemy_count, respawn_coin_count):
	global A0, A1
	A0 = statistics.mean(A0) if len(A0) else 0
	A1 = statistics.mean(A1) if len(A1) else 0
	A2 = coin_count
	A3 = destroyed_enemy_count
	A4 = shots_count
	A5 = A4 - A3
	A6 = level
	A7 = keyX_pressed_count
	A8 = keyY_pressed_count
	A9 = respawn_enemy_count
	A10 = respawn_coin_count
	if sum([A0, A1, A2, A3, A4, A5]) != 0:
		with open("train_data.txt", "a") as file_object:
			file_object.write(",".join(map(str, [A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, A10])))
			file_object.write("\n")

# --------------------
# Full Game Play Loop
# --------------------

quit_game = False
while not quit_game:

	# Start manu
	quit_game = menu()

	# Game settings
	num_of_enemies	= 5				# recommended: 5
	num_of_coins	= 5				# recommended: 5
	level_change	= 1000			# recommended: 1000
	level_score_increase = 10
	level_enemy_increase = 5

	# initialize other variables / counters
	score 		 = 0
	level		 = 1			# A6
	level_iter	 = 0
	loop_iter	 = 0
	keyX_pressed = 0
	keyY_pressed = 0
	game_over 	 = False
	go_to_menu 	 = False

	coin_count = 0				# A2
	destroyed_enemy_count = 0	# A3
	shots_count = 0				# A4
	keyX_pressed_count = 0		# A7
	keyY_pressed_count = 0		# A8
	respawn_enemy_count = 0		# A9
	respawn_coin_count = 0		# A10

	backgound_Y_lower = 0
	backgound_Y_upper = backgound_Y_lower - background_image_hight
	upper_index = 0
	lower_index = 1


	# initialize player and bullet
	player = SpaceShip(player_image, explosion_image[0], screen_sizeX/2-32, screen_sizeY-100)
	bullet = Bullet(bullet_image, explosion_image[0], speedY = -bullet_speed, sound = bullet_sound, state = 'hide', sizeX = 32, sizeY = 32)

	# initialize enemies
	enemy = []
	enemy_image_index = 0
	for i in range(num_of_enemies):
		enemy.append(SpaceEnemy(enemy_image[enemy_image_index], explosion_image[1], speedY = level, hit_points = level))
		respawn(enemy[i], level)
		respawn_enemy_count += 1

	# initialize coins
	coins = []
	for i in range(num_of_coins):
		coins.append(SpaceCoin(coin_image, explosion_image[0], speedY = level, hit_points = 1))
		respawn(coins[i], level)
		respawn_coin_count += 1

	# initialize collection data
	thread = None
	A0 = []
	A1 = []
	A2 = 0
	A3 = 0
	A4 = 0
	A5 = 0
	A6 = 0
	A7 = 0
	A8 = 0
	A9 = 0
	A10 = 0
	thread_collect_data()
	new_user_type = None

	# --------------------
	# Main Game Play Loop
	# --------------------

	while not go_to_menu and not quit_game:

		# Fill screen and background image	
		screen.fill(background_color)

		# Background images moving
		backgound_Y_lower += 1
		backgound_Y_upper += 1
		if backgound_Y_lower > screen_sizeY:
			backgound_Y_lower = backgound_Y_upper
			backgound_Y_upper = backgound_Y_lower - background_image_hight
			temp = upper_index
			upper_index = lower_index
			lower_index = temp
		screen.blit(background_image[upper_index], (0,backgound_Y_upper))
		screen.blit(background_image[lower_index], (0,backgound_Y_lower))

		# check if increase level
		level_iter += 1
		if level_iter > level_change and not game_over:
			level_iter = 0
			level += 1

			# increase number of enemies with higher speed
			enemy_image_index = (level -1) % len(enemy_image)
			for i in range(num_of_enemies, num_of_enemies+level_enemy_increase):
				enemy.append(SpaceEnemy(enemy_image[enemy_image_index], explosion_image[1], speedY = level, hit_points = level))
				respawn(enemy[i], level)
				respawn_enemy_count += 1
			num_of_enemies	+= level_enemy_increase

			# increase number of coin with same speed
			for i in range(num_of_coins, num_of_coins + num_of_coins):
				coins.append(SpaceCoin(coin_image, explosion_image[0], speedY = level, hit_points = 1))
				respawn(coins[i], level)
				respawn_coin_count += 1

			# increase score when reaching new level
#			score += level_score_increase

		# Check events and take action
		for event in pygame.event.get():	
			if event.type == pygame.QUIT:
				quit_game = True	

			# if key is pressed
			if event.type == pygame.KEYDOWN:
				
				# if Game Over and any key, go to menu 				
				if game_over:
					go_to_menu = True

				# 'p' or ESC' for pause 
				elif event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
				 	paused(screen_sizeX, screen_sizeY)

				# 'arrow keys' for movement
				elif event.key == pygame.K_LEFT:
					player.speedX = -player_maxSpeedX
					keyX_pressed += 1
					keyX_pressed_count += 1
				elif event.key == pygame.K_RIGHT:
					player.speedX = player_maxSpeedX
					keyX_pressed += 1
					keyX_pressed_count += 1
				elif event.key == pygame.K_UP:
					player.speedY = -player_maxSpeedY
					keyY_pressed += 1
					keyY_pressed_count += 1
				elif event.key == pygame.K_DOWN:
					player.speedY = player_maxSpeedY
					keyY_pressed += 1
					keyY_pressed_count += 1

				# if space key, fire bullet			
				elif (event.key == pygame.K_SPACE or event.key == pygame.K_a) and bullet.state == 'hide':
					bullet.fire_bullet(player)
					shots_count += 1
					

			# if key is released, stop movement in a nice way
			if event.type == pygame.KEYUP:
				if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
					keyX_pressed -= 1
					if keyX_pressed == 0:
						player.speedX = 0
				if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
					keyY_pressed -= 1
					if keyY_pressed == 0:
						player.speedY = 0

		# Move player and check not out of screen
		player.update_player_postion(screen_sizeX, screen_sizeY)
		bullet.update_bullet_position(screen_sizeX, screen_sizeY)

		if game_over:
			player.explosion_counter = 0
			thread.cancel()
			user_type = prediction_user_type(level, keyX_pressed_count, keyY_pressed_count, respawn_enemy_count, respawn_coin_count)
			show_game_over(screen_sizeX, screen_sizeY, score, session_high_score, coin_count, user_type)
			show_score(score, level, PLAYER_NAME, coin_count, game_over=True)
			show_online_score()
		else:
			
			# Move enemies and check collisions
			for i in range(num_of_enemies):
				
				# if enemy exploding
				if enemy[i].explosion_counter >= 1:
					enemy[i].explosion_counter -= 1
				elif enemy[i].explosion_counter == 0:
					respawn(enemy[i], level)
					respawn_enemy_count += 1
				else:
					enemy[i].update_enemy_position(screen_sizeX, screen_sizeY)
					if enemy[i].posY > screen_sizeY:
						respawn(enemy[i], level)
						# respawn_enemy_count += 1
					enemy[i].show()
					
					# if enemy collision with player
					if is_collision(enemy[i], player):
						explosion_sound.play()
						player.explosion_counter = 5
						if score > session_high_score:
							session_high_score = score
						game_over = True
					
					# if bullet hits enemy 
					elif bullet.state == 'show' and is_collision(enemy[i], bullet) :
						explosion_sound.play()
						enemy[i].explosion_counter = 10
						score += enemy[i].hit_points
						destroyed_enemy_count += 1
						bullet.state = 'hide'

				enemy[i].show()

			# Move coins and check collisions
			for i in range(num_of_coins):
				
				# if coin exploding
				if coins[i].explosion_counter >= 1:
					coins[i].explosion_counter -= 1
				elif coins[i].explosion_counter == 0:
					respawn(coins[i], level)		
					respawn_coin_count += 1
				else:
					coins[i].update_coin_position(screen_sizeX, screen_sizeY)
					if coins[i].posY > screen_sizeY:
						respawn(coins[i], level)
						# respawn_coin_count += 1
					coins[i].show()

					# if coin collision with player
					if is_collision(coins[i], player):
						coins[i].explosion_counter = 0
						score += coins[i].hit_points
						coin_count += 1

				coins[i].show()

			# show player
			bullet.show()
			player.show()

			new_user_type = new_prediction_user_type(level, keyX_pressed_count, keyY_pressed_count, respawn_enemy_count, respawn_coin_count)
			user_type = prediction_user_type(level, keyX_pressed_count, keyY_pressed_count, respawn_enemy_count, respawn_coin_count)
			show_score(score, level, PLAYER_NAME, coin_count, user_type=user_type, new_user_type=new_user_type)
			show_online_score()

		pygame.display.flip()
		
		clock.tick(frames_per_second)

		if player.explosion_counter > 0 :
			# to freeze and show player explosion longer
			time.sleep(1)

	# Update High Score database
	if score > 0:
		high_scores.high_scores_update_db(db_connection, PLAYER_NAME, score)

	save_collection_data(level, keyX_pressed_count, keyY_pressed_count, respawn_enemy_count, respawn_coin_count)

db_connection.close()
print('Successfully quit Space Wars!')
