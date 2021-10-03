# --------------------------------------------------------------------------------
#
# AirHockey.py for LEGO Mindstorms 51515
#
# By Chun Cheung Yim (cheungslegocreation@gmail.com)
#
# https://www.youtube.com/channel/UCbp55xmp7t4dhIjeSHD8FwA
#
# This work is licensed to you under the terms defined in Creative Commons Attribution-NonCommercial-NoDerivs (CC BY-NC-ND).
# For more details on what this means, refer to
#
# https://creativecommons.org/licenses/by-nc-nd/4.0/
#
# --------------------------------------------------------------------------------

import hub
import utime
import sys
import urandom
import math


# global logging function
def log(s):
    pass
    print(s)


# define the direction vector the puck can travel (from index 0 to 6)
# the index values are - 0 neutral, 1 (top left), 2 (left), 3 (bottom left), 4 (top right), 5 (right), 6 (bottom right)
PUCK_DIR_VECTORS = ((0, 0), (-1, -1), (-1, 0), (-1, 1),(1, -1), (1, 0), (1, 1))


# define a player
class Player:
    # controlMotor - the motor used for obtaining the control block position
    # strikerX - the x value where this player's sticker is located
    # isPlayer1 - True if the player created is the first player, False otherwise
    def __init__(self, controlMotor, strikerX, isPlayer1):
        self._controlMotor = controlMotor
        # set absolute position
        self._controlMotor.mode(3)
        # reset the control motor to 0
        x = self._controlMotor.get()[0]
        self._controlMotor.preset(x)
        self._controlMotor.run_to_position(0, 20)
        utime.sleep_ms(1000)
        self._controlMotor.preset(0)
        # allow the motor to flow when stop
        self._controlMotor.float()
        # reset the current striker position
        self._strikerX = strikerX
        self._strikerY = 2
        self._isPlayer1 = isPlayer1

    # Return the striker position in (x, y) format (the value of y is in [0..4])
    def getStrikerPos(self):
        y = self._controlMotor.get()[0] # the valu eis between 0 to 359
        if (y > 180):
            y = y - 360
        # now set the striker y position
        if (y > 45):
            if (self._isPlayer1):
                self._strikerY = 0
            else:
                self._strikerY = 4
        elif (y > 15 and y <= 45):
            if (self._isPlayer1):
                self._strikerY = 1
            else:
                self._strikerY = 3
        elif (y >= -15 and y <= 15):
            if (self._isPlayer1):
                self._strikerY = 2
            else:
                self._strikerY = 2
        elif (y < -15 and y >= -45):
            if (self._isPlayer1):
                self._strikerY = 3
            else:
                self._strikerY = 1
        elif (y < -45):
            if (self._isPlayer1):
                self._strikerY = 4
            else:
                self._strikerY = 0
        # return the striker position
        return (self._strikerX, self._strikerY)


# define a puck that can be hit by the striker
class Puck:
    # tableWidth - width of the table
    # x, y - the initial (x,y) coordinates of the puck.
    # dir - # 7 values possible - 0 (neutral), 1 (top left), 2 (left), 3 (bottom left), 4 (top right), 5 (right), 6 (bottom right)
    # striker - 0: not attached, 1: striker 1, 2: striker 2
    def __init__(self, tableWidth, x, y, dir = 0, striker = 0):
        self._tableWidth = tableWidth
        self._x = x
        self._y = y
        self._dir = dir
        self._striker = striker

    # return the position of the puck - (x, y, dir, striker)
    def getStatus(self):
        return (self._x, self._y, self._dir, self._striker)

    # set the position of the puck and its travelling direction
    def setStatus(self, x, y, dir = None, striker = None):
        self._x = x
        self._y = y
        if (dir != None):
            self._dir = dir
        if (striker != None):
            self._striker = striker

    def getX(self):
        return self._x

    def getY(self):
        return self._y

    def getDir(self):
        return self._dir

    def getStriker(self):
        return self._striker

    # Move the puck based on the information stored in x, y, dir. Note that the direction could change
    # based on the bouncing of the puck on the wall.
    # 1 - 4
    # 2 0 5
    # 3 - 6
    # vsBrick - True - if play against brick
    def move(self, vsBrick = True):
        if (self._dir == 0):
            return
        self._x = self._x + PUCK_DIR_VECTORS[self._dir][0]
        self._y = self._y + PUCK_DIR_VECTORS[self._dir][1]
        # prevent the puck from moving out of bound
        if (self._y < 0):
            self._y = 0
        if (self._y > 4):
            self._y = 4
        # if bounce against the side wall, need to change direction
        if (self._y == 0):
            if (self._dir == 1):
                self._dir = 3
            elif (self._dir == 4):
                self._dir = 6
        elif (self._y == 4):
            if (self._dir == 3):
                self._dir = 1
            elif (self._dir == 6):
                self._dir = 4
        log("puck pos - x: " + str(self._x) + " y: " + str(self._y) + " dir: " + str(self._dir))


# define a game of air hockey
class AirHockey:
    # The brightness of the elements that will be shown on the play table
    # tableWidth - width of the table, must be odd number (at tableWidth / 2 print the mid field line)
    # puckBrightness - brightness use for the puck
    # strikerBrightness - brightness use for the striker
    # playerCount - 1 or 2 - number of users playing the game
    # constSpeed - True or False - the puck should run at a constant speed or not
    # minSpeed - minimum speed the puck will run at (minimum speed will have a higher delay in ms)
    # maxSpeed - maximum speed the puck will run at (minimum speed will have a lower delay in ms)
    # speedIncrement - speed the puck will be increased by until reaching the minSpeed
    # skillLevel - a value between 0 to 100 indicate the likelihood the computer can strike the puck in 1 player mode (100 means 100% hit rate)
    # gameCount - max number of games to play before exiting
    def __init__(self, tableWidth = 20, puckBrightness = 6, strikerBrightness = 8, playerCount = 1, constSpeed = False, minSpeed = 500, maxSpeed = 50, speedIncrement = 50, skillLevel = 80, gameCount = 3):
        self._tableWidth = tableWidth
        self._puckBrightness = puckBrightness
        self._strikerBrightness = strikerBrightness
        self._player1 = Player(hub.port.F.motor, self._tableWidth - 1, True)
        self._player2 = Player(hub.port.E.motor, 0, False)
        self._playerCount = playerCount
        self._constSpeed = constSpeed
        self._minSpeed = minSpeed
        self._maxSpeed = maxSpeed
        self._speedIncrement = speedIncrement
        self._skillLevel = skillLevel
        self._imgBackground = hub.Image("13131:31313:13131:31313:13131")
        self._gameCount = gameCount
        self._gamesPlayed = 0
        self._gamesWonByPlayer1 = 0
        self._img1Player = hub.Image("77770:70007:77770:70007:77770")
        self._img2Player = hub.Image("00900:77777:80708:08080:08080")
        self._gameImages = [hub.Image("00900:09900:00900:00900:09990"), hub.Image("09990:00090:09990:00090:09990"), hub.Image("09990:09000:09990:00090:09990"), hub.Image("09990:00090:00900:00900:00900"), hub.Image("09990:09090:09990:00090:09990")]
        hub.sound.volume(80)

    # Refresh the screen of the air hockey table.
    # p1 - player 1 pos information (x,y)
    # p2 - player 2 pos information (x,y)
    # ps - status of the puck (self._x, self._y, self._dir, self._striker)
    def refreshScreen(self, p1, p2, ps):
        # clear the screen
        hub.display.show(self._imgBackground)
        # display striker position + puck position for player 2
        if (ps[0] <= 4):
            hub.display.pixel(ps[0], ps[1], self._puckBrightness)
            hub.display.pixel(0, p2[1], self._strikerBrightness)
        # display striker position + puck position for player 1
        elif (ps[0] >= (self._tableWidth - 5)):
            hub.display.pixel(ps[0] % 5, ps[1], self._puckBrightness)
            hub.display.pixel(4, p1[1], self._strikerBrightness)
        else:
            hub.display.pixel(ps[0] % 5, ps[1], self._puckBrightness)

    # Generate a direction vector when player 1 strikes.
    # returns a direction vector value.
    def p1strike(self):
        return 1 + (urandom.randrange(0, 100) % 3)

    # Generate a direction vector index when player 1 strikes.
    def p2strike(self):
        return 4 + (urandom.randrange(0, 100) % 3)

    # update the speed of the puck based on init. settings
    def updatePuckSpeed(self):
        # game to be played at constant speed?
        if (self._constSpeed):
            self._currentSpeed = self._minSpeed
            return
        # no, play at increasing speed
        if (self._initialSpeedSet):
            self._currentSpeed = self._minSpeed
            self._initialSpeedSet = False
            return
        self._currentSpeed = self._currentSpeed - self._speedIncrement
        if (self._currentSpeed < self._maxSpeed):
            self._currentSpeed = self._maxSpeed

    # create an animation on the screen to flash a player has lost
    # loser - 1 or 2 (for player 1 and player 2)
    # times - number of times the animation shows
    def flashLoser(self, loser, times = 3):
        playerY = [self._player1._strikerY, [self._computerY, self._player2._strikerY][self._playerCount == 2]][loser - 1]
        puckX = [4, 0][loser - 1]
        puckY = self._puck.getY()
        for x in range(0, times):
            hub.display.show(self._imgBackground)
            hub.display.pixel(puckX, puckY, self._puckBrightness)
            hub.display.pixel(puckX, playerY, self._strikerBrightness)
            utime.sleep_ms(500)
            # flash the loser background
            hub.display.show(self._imgBackground)
            for y in range(0, 5):
                hub.display.pixel(puckX, y, 7)
            hub.display.pixel(puckX, puckY, self._puckBrightness)
            hub.display.pixel(puckX, playerY, self._strikerBrightness)
            utime.sleep_ms(500)

    # flashes the colour of the winner
    # winnerIndex - 1 or 2 (for player 1 or player 2)
    def showWinner(self, winnerIndex):
        # play the loser beeps
        s4 = [400, 200]
        for x in s4:
            hub.sound.beep(x)
            utime.sleep_ms(300)
        # flash the loser pos
        if (winnerIndex == 1):
            self.flashLoser(2)
        elif (winnerIndex == 2):
            self.flashLoser(1)
        # show winner colour
        winnerColour = (0, 6, 3) # off, green, blue
        for x in range(0, 3):
            hub.led(winnerColour[winnerIndex])
            utime.sleep_ms(500)
            hub.led(0)
            utime.sleep_ms(500)

    # return the next Y position of the puck based on its current travelling direction
    # 1 - 4
    # 2 0 5
    # 3 - 6
    # vsBrick - True - if play against brick
    def calculatePuckNextY(self):
        y = self._puck.getY()
        d = self._puck.getDir()
        # puck is going left only
        if (d == 2):
            return y
        if (y >= 1 and y <= 3):
            if (d == 1):
                return y - 1
            else:
                # d == 3 here
                return y + 1
        if (y == 0 and d == 3):
            return 1
        if (y == 4 and d == 1):
            return 3
        return y

    # Reset all the parameters relating to the game so it can be started
    # player1Start - if True, player 1 should start the game, if False, player 2 starts the game
    def resetGame(self, player1Start):
        self._initialSpeedSet = True
        self._computerY = 2
        self._currentSpeed = self._minSpeed
        puckX = [1, self._tableWidth - 2][player1Start]
        attachedToPlayer = [2, 1][player1Start]
        self._puck = Puck(self._tableWidth, puckX, 2, 0, attachedToPlayer)

    # Display animation for the final match winner
    # winner - 1 or 2
    def showMatchWinner(self, winner):
        winnerColour = [6, 3][winner - 1]
        hub.display.clear()
        # change the light to represent winner colour
        hub.led(winnerColour)
        # display a trophy
        for x in range(0, 3):
            hub.display.show([hub.Image("09990:07770:03530:00500:06660")], fade = 5, delay = 1000)
            utime.sleep_ms(500)
        # turn off the light
        hub.led(0)

    # display the end game message and exit the program.
    # userInitiatedExit - True, if the game finished due to user initiated exit. False if the match
    # has finished due to all players have completed all the games.
    def endGame(self, userInitiatedExit = False):
        hub.display.clear()
        if (userInitiatedExit):
            sys.exit(0)
        # players have completed the match, show the final result
        if (self._gamesWonByPlayer1 > (self._gameCount - self._gamesWonByPlayer1)):
            # player 1 won
            self.showMatchWinner(1)
        else:
            # player 2 won
            self.showMatchWinner(2)
        sys.exit(0)

    # display title animation
    def displayTitleAnimation(self):
        # show title animation
        hub.display.show([hub.Image("00900:09090:90009:00000:00000"), hub.Image("90009:99999:90009:00000:00000")], fade = 2, delay = 1000)
        utime.sleep_ms(1000)
        hub.display.clear()
        # show the bounce sequence
        hub.display.show([
        hub.Image("00000:00000:97009:00000:00000:"),
        hub.Image("00000:00000:90709:00000:00000:"),
        hub.Image("00000:00000:90079:00000:00000:"),
        hub.Image("00000:00000:00009:90070:00000:"),
        hub.Image("00000:00000:00009:90000:00700:"),
        hub.Image("00000:00000:00009:97000:00000:"),
        hub.Image("00000:00000:00709:90000:00000:"),
        hub.Image("00000:00079:00000:90000:00000:"),
        hub.Image("00000:00709:90000:00000:00000:"),
        hub.Image("00000:97009:00000:00000:00000:"),
        hub.Image("00000:90709:00000:00000:00000:"),
        hub.Image("00000:90079:00000:00000:00000:"),
        hub.Image("00000:00009:00700:90000:00000:"),
        hub.Image("00000:00009:00000:97000:00000:"),
        hub.Image("00000:00000:00000:90709:00000:"),
        hub.Image("00000:00000:00000:90079:00000:")
        ], delay = 300)
        # show title animation
        hub.display.show([hub.Image("00900:09090:90009:00000:00000"), hub.Image("90009:99999:90009:00000:00000")], fade = 2, delay = 1000)
        utime.sleep_ms(1000)
        hub.display.clear()

    # select the number of players in the game
    def selectPlayers(self):
        # set the number of players depending on the position of the player 1 wheel
        while (True):
            if (hub.button.left.is_pressed()):
                self.endGame(True)
                return
            pos = self._player1.getStrikerPos()
            if (pos[1] < 2):
                hub.display.show(self._img1Player)
            else:
                hub.display.show(self._img2Player)
            # if the right key button is pressed, return the number of players
            if (hub.button.right.is_pressed()):
                hub.sound.beep(1000, 200)
                return [2, 1][pos[1] < 2]

    # set the number of games to play
    def setGameCount(self):
        # set the number of games to play by turning the player 1 wheel
        while (True):
            if (hub.button.left.is_pressed()):
                self.endGame(True)
                return
            pos = self._player1.getStrikerPos()
            hub.display.show(self._gameImages[pos[1]])
            # if the right key button is pressed, return the number of players
            if (hub.button.right.is_pressed()):
                hub.sound.beep(1000, 200)
                return pos[1] * 2 + 1

    # start a game
    def run(self):
        self.displayTitleAnimation()
        self._playerCount = self.selectPlayers()
        utime.sleep_ms(1000)
        self._gameCount = self.setGameCount()
        utime.sleep_ms(1000)

        # no game has been played
        self._gamesWonByPlayer1 = 0
        lastWinner = -1
        while (self._gamesPlayed < self._gameCount):
            # check if the exit button has been pressed
            if (hub.button.left.is_pressed() or lastWinner == 0):
                self.endGame(True)
                return
            # if the last winner hasn't been defined or the last winner is player 2,
            # let player 1 to start first
            if (lastWinner == -1 or lastWinner == 2):
                self.resetGame(True)
                lastWinner = self.startGame()
            elif (lastWinner == 1):
                self.resetGame(False)
                lastWinner = self.startGame()
            # check who won the last game
            if (lastWinner == 1):
                self._gamesWonByPlayer1 = self._gamesWonByPlayer1 + 1
            # update the number of games played
            self._gamesPlayed = self._gamesPlayed + 1
        # all games have been played
        self.endGame(False)

    # Start a new game, returns
    # 0 - if the user hit the left button to quit the game
    # 1 - if player 1 won the game
    # 2 - if player 2 won the game
    def startGame(self):
        while (True):
            # quit if the left button is pressed
            if (hub.button.left.is_pressed()):
                hub.display.clear()
                return 0

            # move the puck
            self._puck.move()

            # get the position for striker 1, 2 and the puck
            s1pos = self._player1.getStrikerPos()
            # use pre-computed position
            if (self._playerCount == 1):
                s2pos = (0, self._computerY)
            else:
                s2pos = self._player2.getStrikerPos()

            # check if the puck is attached to the striker, if so, need to update the y position of the puck
            puckStriker = self._puck.getStriker()
            if (puckStriker == 1):
                self._puck.setStatus(self._puck.getX(), s1pos[1], 0, 1)
            elif (puckStriker == 2 and self._playerCount == 2):
                self._puck.setStatus(self._puck.getX(), s2pos[1], 0, 2)

            # if the puck is attached and RB is pressed, hit the puck
            # return (self._x, self._y, self._dir, self._striker)
            if (hub.button.right.is_pressed() == True):
                if (puckStriker == 1):
                    self._puck.setStatus(self._puck.getX(), self._puck.getY(), self.p1strike(), 0)
                elif (puckStriker == 2):
                    self._puck.setStatus(self._puck.getX(), self._puck.getY(), self.p2strike(), 0)
                # make a sound when someone hits the puck
                if (puckStriker != 0):
                    hub.sound.beep(1000, 100)

            # refresh the screen
            puckStatus = self._puck.getStatus()
            self.refreshScreen(s1pos, s2pos, puckStatus)

            # the puck has reached the player 1 and player 1's y position doesn't matches the pucks, player1 loses
            if (self._puck.getStriker() == 0):
                if (self._puck.getX() == (self._tableWidth - 1)):
                    if (s1pos[1] != self._puck.getY()):
                        self.showWinner(2)
                        return 2
                    else:
                        # player 1 can block it, generate a random return hit
                        self._puck.setStatus(self._puck.getX(), self._puck.getY(), self.p1strike(), 0)
                        hub.sound.beep(500, 100)
                        # increase the play speed
                        self.updatePuckSpeed()

                # 2 player mode?
                elif (self._playerCount == 2):
                    if (self._puck.getX() == 0):
                        if (s2pos[1] != self._puck.getY()):
                            self.showWinner(1)
                            return 1
                        else:
                            # player 2 can block it, generate a random return hit
                            self._puck.setStatus(self._puck.getX(), self._puck.getY(), self.p2strike(), 0)
                            hub.sound.beep(700, 100)

                # single player mode - player 2 is the computer player
                # depending on the skill level, move p2 striker to block it
                else:
                    # make the computer to move to a position where it can block the puck when the puck gets to x position of 0.
                    if (self._puck.getX() == 1):
                        r = urandom.randint(0, 100)
                        log('skill: ' + str(r))
                        if (r <= self._skillLevel):
                            # computer player must be able to block the puck
                            self._computerY = self.calculatePuckNextY()
                            log('computer y: ' + str(self._computerY))
                        else:
                            # computer player would not block the puck
                            nextPos = self.calculatePuckNextY()
                            if (nextPos == 0):
                                self._computerY = 1
                            else:
                                self._computerY = nextPos - 1
                    # make a decision to see if computer can block or not
                    elif (self._puck.getX() == 0):
                        if (s2pos[1] != self._puck.getY()):
                            self.showWinner(1)
                            return 1
                        else:
                            # player 2 can block it, generate a random return hit
                            self._puck.setStatus(self._puck.getX(), self._puck.getY(), self.p2strike(), 0)
                            hub.sound.beep(700, 100)

            # add a delay based on the current speed
            utime.sleep_ms(self._currentSpeed)
            log('current speed: ' + str(self._currentSpeed))


# create a new game
game = AirHockey(tableWidth = 20, puckBrightness = 8, strikerBrightness = 9, playerCount = 1, constSpeed = False, minSpeed = 300, maxSpeed = 100, speedIncrement = 25, skillLevel = 90, gameCount = 3)
game.run()