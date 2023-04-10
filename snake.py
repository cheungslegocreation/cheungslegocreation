# --------------------------------------------------------------------------------
#
# Snake.py for LEGO Mindstorms 51515
#
# By Chun Cheung Yim (cheungslegocreation @ g m a i l.com)
#
# https://www.youtube.com/c/cheungslegocreation
#
# This work is licensed to you under the terms defined in Creative Commons Attribution-NonCommercial-NoDerivs (CC BY-NC-ND).
# For more details on what this means, refer to
#
# https://creativecommons.org/licenses/by-nc-nd/4.0/
#
# --------------------------------------------------------------------------------

from mindstorms import MSHub, Motor, MotorPair, ColorSensor, DistanceSensor, App
from mindstorms.control import wait_for_seconds, wait_until, Timer
import math
import sys
import urandom


# the Snake class
class Snake:

    # class constructor
    # speed - the speed of the game. The closer to 0 the faster the game is.
    def __init__(self, speed):
        self._body = [(0, 0)]        # the body of the snake, the coordinates are in (x, y)
        self._direction = 1        # 1 - right, 2 - down, 3 - left, 4 - up
        self._food_pos = (-1, -1)    # the current position of the food
        self._motor = Motor('E')    # to allow the snake going up and down
        self._hub = MSHub()        # hub class for lots of things :)
        self._motor.set_degrees_counted(0)# reset the motor degree count
        self._points = 0            # number of food eaten
        self._speed = speed        # the speed of the game


    # retrieve the next direction the snake is heading based on button press and motor rotation
    def getNextDirectionFromKey(self):
        if (self._hub.left_button.was_pressed()):
            return 3
        if (self._hub.right_button.was_pressed()):
            return 1
        temp = self._motor.get_degrees_counted()
        if (temp >= 20 and temp < 180):
            return 4
        if (temp > -180 and temp <= -20):
            return 2
        # no change detected, return the current direction, also reset the motor's current degree
        # value for detecting the next round of up/down movement
        return self._direction

    # show the body of the snake
    def show(self):
        self._hub.light_matrix.off()
        isHead = True
        # print the body of the snake
        for (x, y) in self._body:
            if (isHead):
                self._hub.light_matrix.set_pixel(x, y, 80)
                isHead = False
            else:
                self._hub.light_matrix.set_pixel(x, y, 70)
        # print the food position
        if (self._food_pos[0] >= 0 and self._food_pos[1] >= 0):
            self._hub.light_matrix.set_pixel(self._food_pos[0], self._food_pos[1], 100)

    # generate the next food position
    def getNextFoodPos(self):
        # the generated food position should not be in the body of the snake
        (x, y) = (urandom.randrange(0, 100) % 5, urandom.randrange(0, 100) % 5)
        while (True):
            if ((x, y) in self._body):
                (x, y) = (urandom.randrange(0, 100) % 5, urandom.randrange(0, 100) % 5)
            else:
                self._food_pos = (x, y)
                return

    # update the body based on it's current head position and also the direction
    # the head is heading
    def updateBody(self, dir):
        (x, y) = self._body[0]
        if (dir == 1):# right
            x = x + 1
        elif (dir == 2): # down
            y = y + 1
        elif (dir == 3): # left
            x = x - 1
        elif (dir == 4): # up
            y = y - 1

        self._body.insert(0, (x, y))
        if (self._food_pos == (x, y)):
            self._points = self._points + 1
            self._hub.speaker.beep(60, 0.2, 100)
            self._body = self._body[:11]    # limit the length of the snake to 11 (including the head)
            self.getNextFoodPos()
        else:
            # remove the tail
            del self._body[-1]

    # check if the game has reached an exit condition, it could be either
    # 1. the current head position is out of bound
    # 2. the snake's head is actually in the snake's body when the snake is at least 2 units in length (including the head)
    # returns True if the any of the exit condition has been reached, otherwise False
    def exitConditionReached(self):
        (x, y) = self._body[0]
        # condition 1
        if ((x < 0 or x > 4) or (y < 0 or y > 4)):
            return True
        # condition 2
        if len(self._body) > 1:
            (head, *body) = self._body
            # print(str(x)+','+str(y)+'->'+str(body))
            if (x, y) in body:
                return True
        return False

    # print title sequence
    def openingTitleSequence(self):
        # render the opening sequence
        for c in range(0, 3):
            for i in range(0, 5):
                self._hub.light_matrix.show_image('SNAKE', 20 * (i + 1))
                wait_for_seconds(0.2)
        for i in range(3, 0, -1):
            self._hub.light_matrix.write(i)
            self._hub.speaker.beep(70, 0.25, 80)
            wait_for_seconds(1)
        self._hub.speaker.beep(90, 0.25, 80)

    # start the game
    def run(self):
        exit = False
        self.openingTitleSequence()
        self.getNextFoodPos()
        self.show()
        while (exit == False):
            self._direction = self.getNextDirectionFromKey()
            self._motor.set_degrees_counted(0)
            self.updateBody(self._direction)
            if self.exitConditionReached():
                exit = True
                self._hub.light_matrix.show_image('SKULL')
                self._hub.speaker.play_sound('Oh Oh', 100)
                self._hub.light_matrix.off()
                self._hub.light_matrix.write(str(self._points))
                wait_for_seconds(1)
            else:
                self.show()
                wait_for_seconds(self._speed)

# start the game
snake = Snake(0.3)
snake.run()
sys.exit()