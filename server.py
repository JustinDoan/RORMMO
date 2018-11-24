import socket
import pickle
import random
import string
import pygame
from threading import Thread

class Wall(pygame.sprite.Sprite):
    def __init__(self, width, height):
        """ Platform constructor. Assumes constructed with user passing in
            an array of 5 numbers like what's defined at the top of this
            code. """
        super().__init__()

        self.image = pygame.Surface([width, height])
        self.rect = self.image.get_rect()

class Platform(pygame.sprite.Sprite):
    """ Platform the user can jump on """

    def __init__(self, width, height):
        """ Platform constructor. Assumes constructed with user passing in
            an array of 5 numbers like what's defined at the top of this
            code. """
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.grass = pygame.Surface([width,height/2])
        self.dirt = pygame.Surface([width,height/2])
        self.image.blit(self.grass, self.image.get_rect().topleft)
        self.image.blit(self.dirt, self.image.get_rect().bottomleft)
        self.rect = self.image.get_rect()

class LevelManager():

    def __init__(self):

        self.LevelPlayerList = []

    def addLevel(self, level):
        players = []
        LevelPlayerPair = [level, players]
        self.LevelPlayerList.append(LevelPlayerPair)

    def addPlayerToLevel(self, level, player):

        for pair in self.LevelPlayerList:
            if pair[0] == level:
                pair[1].append(player)



class Level():

    def __init__(self, levelData):

        self.LevelData = levelData
        self.Width = 0
        for line in self.LevelData:
            if len(line) > self.Width:
                self.Width = len(line)
        self.Width = (self.Width * 25)-25
        self.Height = len(self.LevelData) * 25
        #These we can keep track on a level by level basis
        self.Enemies = []
        self.TemporaryObjects = []
        self.platform_list = pygame.sprite.Group()

    def update(self):
        for Enemy in self.Enemies:
            Enemy.update()
        for TempObject in self.TemporaryObjects:
            TempObject.update()

    def build(self):
        for row_num, row in enumerate(self.LevelData):
            for tile_num,tile in enumerate(row):
                if tile == 1:
                    block = Wall(25, 25)
                    block.rect.x = (tile_num)*(25)
                    block.rect.y = (row_num)*(25)
                    #block.player = self.player
                    self.platform_list.add(block)
                if tile == 2:
                    block = Platform(25, 25)
                    block.rect.x = (tile_num)*(25)
                    block.rect.y = (row_num)*(25)
                    #block.player = self.player
                    self.platform_list.add(block)





#We want to send updates to all players of other player locations every 30 ticks, as since this will be pve there is no need for speed.
#this player class will track everything that we need to track for each player
class Player(pygame.sprite.Sprite):

    #When we get a new player connection
    def __init__(self,addr, username, level):

        super().__init__()
        self.addr = addr
        self.username  = username
        self.uniqueID = ""
        for x in range(10):
            self.uniqueID = self.uniqueID + str(random.randint(0,9))
            self.uniqueID = self.uniqueID + random.choice(string.ascii_letters)
        self.uniqueID = hash(self.uniqueID)
        self.level = level
        #This positioning is within the level.
        self.xPos = 325
        self.yPos = level.Height -200
        self.change_x = 0
        self.change_y = 0
        #So we can be aware of any updates
        #this is for tracking bounding boxes
        self.width = 20
        self.height = 30
        self.rect = pygame.Rect(self.xPos,self.yPos,self.width,self.height)
        self.previousDataPack = ""

    def getPosition(self):
        return self.rect

    def getDataPack(self):
        dataPack = {
        'type': "positionUpdate",
        'playerPosition': self.getPosition(),
        'username': self.username
        }
        #if dataPack == self.previousDataPack:
        #    return False
        #self.previousDataPack = dataPack
        return dataPack

    def move(self, keyPressed):
        #Here is where we keep track of the players movement
        if keyPressed == "L":
            self.go_left()
        if keyPressed == "R":
            self.go_right()
        if keyPressed == "U":
            self.jump()
        if keyPressed == "S":
            self.stop()

    def update(self):
        """ Move the player. """
        # Gravity
        self.calc_grav()

        # Move left/right
        self.rect.x += self.change_x

        # See if we hit anything
        block_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        for block in block_hit_list:
            # If we are moving right,
            # set our right side to the left side of the item we hit
            if self.change_x > 0:
                self.rect.right = block.rect.left
            elif self.change_x < 0:
                # Otherwise if we are moving left, do the opposite.
                self.rect.left = block.rect.right

        # Move up/down
        self.rect.y += self.change_y

        # Check and see if we hit anything
        block_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        for block in block_hit_list:

            # Reset our position based on the top/bottom of the object.
            if self.change_y > 0:
                self.rect.bottom = block.rect.top
            elif self.change_y < 0:
                self.rect.top = block.rect.bottom

            # Stop our vertical movement
            self.change_y = 0


    def calc_grav(self):
        """ Calculate effect of gravity. """
        if self.change_y == 0:
            self.change_y = 1
        else:
            self.change_y += .35

        # See if we are on the ground.
        if self.rect.y >= self.level.Height - self.rect.height and self.change_y >= 0:
            self.change_y = 0
            self.rect.y = self.level.Height - self.rect.height

    def jump(self):
        """ Called when user hits 'jump' button. """

        # move down a bit and see if there is a platform below us.
        # Move down 2 pixels because it doesn't work well if we only move down
        # 1 when working with a platform moving down.
        self.rect.y += 2
        platform_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        self.rect.y -= 2

        # If it is ok to jump, set our speed upwards
        if len(platform_hit_list) > 0 or self.rect.bottom >= self.level.Height:
            self.change_y = -10

    # Player-controlled movement:
    def go_left(self):
        """ Called when the user hits the left arrow. """
        self.change_x = -6

    def go_right(self):
        """ Called when the user hits the right arrow. """
        self.change_x = 6

    def stop(self):
        """ Called when the user lets off the keyboard. """
        self.change_x = 0


def PacketAccepter():
    print("Starting Port listening")
    while True:
        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
        #print("CONNECTION HAPPENED FROM: " + addr[0])
        loadedData = pickle.loads(data)

        #print(loadedData)

        #If the user request a level load, we make sure they get it right away.
        thePlayer = ""
        #TODO Rewrite Level Request Response
        if loadedData["type"] == "level":
            print("Player Level Request")
            level = {"level": mainLevel.LevelData}
            data_to_send = pickle.dumps(level)
            sock.sendto(bytes(data_to_send), addr)
        else:
            #Lets check if this incoming packet is from a new player
            #print(len(players))
            if (len(players) == 0):
                print("Added First Player")
                #We automatically add the first player into the player list
                #mainLevel is default level for now
                newPlayer = Player(addr, loadedData["username"], mainLevel)
                players.append(newPlayer)
                levelManager.addPlayerToLevel(mainLevel, newPlayer)
                #When we add a player, we will send them their ID that is generated ServerSide
                idPacket = {
                'type' : "ID",
                'ID': newPlayer.uniqueID
                }
                data_to_send = pickle.dumps(idPacket)
                sock.sendto(bytes(data_to_send), newPlayer.addr)
                thePlayer = newPlayer
            else:
                playerCheckFlag = True
                #print('Checking for existing player')
                for player in players:
                    if loadedData["uniqueID"] == player.uniqueID:
                        thePlayer = player
                        playerCheckFlag = False
                        player.move(loadedData['keyPressed'])
                if playerCheckFlag:
                    print("Added Player: " + loadedData["username"])

                    newPlayer = Player(addr, loadedData["username"], mainLevel)
                    players.append(newPlayer)
                    levelManager.addPlayerToLevel(mainLevel, newPlayer)
                    idPacket = {
                    'type' : "ID",
                    'ID': newPlayer.uniqueID
                    }
                    data_to_send = pickle.dumps(idPacket)
                    sock.sendto(bytes(data_to_send),newPlayer.addr)
                    thePlayer = newPlayer
        #Once we perform our player exists checks, we can now take the input from the client and use it to update our players position servcer
        #At this point after we check if the player is new or is reconnecting, we can process their movement packets
        #we grab their movement information
        #thePlayer.move(loadedData['keyPressed'])
            #print(str(thePlayer.rect))





        #When we recieve an incoming message, we rebroadcast to
        #all other connections
def PacketSender():
    print("Starting Port Sending")
    while True:
        #Here we create our global packet we send to every player
        #this will eventually be changed to be only the players on the same level.
        for player in players:
            player.update()

        listOfPlayerDataPacks = []
        listOfTemporaryObjectsDataPacks = []
        listOfEnemyDataPacks = []
        for player in players:
            playerDataPack = player.getDataPack()
            if playerDataPack != False:
                listOfPlayerDataPacks.append(playerDataPack)

        data = {
        'type': "updateInformation",
        'playerInformation': listOfPlayerDataPacks,
        'enemyInformation': listOfEnemyDataPacks,
        'temporaryObjectsInformation': listOfTemporaryObjectsDataPacks
        }
        #if data['playerInformation'] or data['enemyInformation'] or data['temporaryObjectsInformation']:
            #Send updates to every connected player on our list of players
        data_to_send = pickle.dumps(data)
        for player in players:
            sock.sendto(bytes(data_to_send), player.addr)
        clock.tick(60)



###Server start up
UDP_IP = ''
UDP_PORT = 5005
clock = pygame.time.Clock()
print("Binding Port")
sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))
print("Successfully Binded Port")
levelData =     [[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,2,2,2,2,2,2,2,2,2,2,1,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,2,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,2,1],
                 [1,0,0,0,0,0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,2,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,0,0,0,0,0,1,0,0,0,0,1,0,1,1,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,1,1,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,1,0,0,0,1],
                 [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]

        ]
#Create Level
print("Creating Level")
mainLevel = Level(levelData)
levelManager = LevelManager()
print("Built Level Manager")
mainLevel.build()
levelManager.addLevel(mainLevel)
#Create Players list which we will use to add players to level.
players = []
print("Finished Building Level and Global Player list")
packetAccepter = Thread(target=PacketAccepter)
packetSender = Thread(target=PacketSender)

packetAccepter.start()
packetSender.start()
