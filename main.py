import pygame
import socket
import pickle
import threading
# Global constants
UDP_IP = "98.204.46.243"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) #Socket
sock.connect((UDP_IP, UDP_PORT))
# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800

class Player(pygame.sprite.Sprite):
    """ This class represents the bar at the bottom that the player
        controls. """

    # -- Methods
    def __init__(self, username, color):
        """ Constructor function """

        # Call the parent's constructor
        super().__init__()
        self.FONT = pygame.font.SysFont('Arial', 10)
        self.FONT_COLOR = pygame.Color('white')
        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        self.width = 20
        self.height = 30
        self.username = username
        self.color = color
        self.image = pygame.Surface([self.width, self.height])
        self.image.fill(self.color)
        self.rect =  self.image.get_rect()

        # Set speed vector of player
        self.change_x = 0
        self.change_y = 0

        # List of sprites we can bump against
        self.level = None


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
        if self.rect.y >= SCREEN_HEIGHT - self.rect.height and self.change_y >= 0:
            self.change_y = 0
            self.rect.y = SCREEN_HEIGHT - self.rect.height

    def jump(self):
        """ Called when user hits 'jump' button. """

        # move down a bit and see if there is a platform below us.
        # Move down 2 pixels because it doesn't work well if we only move down
        # 1 when working with a platform moving down.
        self.rect.y += 2
        platform_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        self.rect.y -= 2

        # If it is ok to jump, set our speed upwards
        if len(platform_hit_list) > 0 or self.rect.bottom >= SCREEN_HEIGHT:
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




class Nametag(pygame.sprite.Sprite):

    def __init__(self, player):

        super().__init__()
        self.player = player
        self.image = self.player.FONT.render(self.player.username, True, self.player.FONT_COLOR)
        self.rect =  self.image.get_rect()


    def update(self):
        self.rect.x = ((-1*(self.image.get_size()[0] - self.player.image.get_size()[0])/2) + self.player.rect.x)
        self.rect.y = self.player.rect.y - 15




class Wall(pygame.sprite.Sprite):
    def __init__(self, width, height):
        """ Platform constructor. Assumes constructed with user passing in
            an array of 5 numbers like what's defined at the top of this
            code. """
        super().__init__()

        self.image = pygame.Surface([width, height])
        self.image.fill(GREEN)

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
        self.grass.fill(GREEN)
        self.dirt = pygame.Surface([width,height/2])
        self.dirt.fill((255,0,0))
        self.image.blit(self.grass, self.image.get_rect().topleft)
        self.image.blit(self.dirt, self.image.get_rect().bottomleft)
        self.rect = self.image.get_rect()


class Level(object):
    """ This is a generic super-class used to define a level.
        Create a child class for each level with level-specific
        info. """

    def __init__(self, player):
        """ Constructor. Pass in a handle to player. Needed for when moving platforms
            collide with the player. """
        self.platform_list = pygame.sprite.Group()
        self.enemy_list = pygame.sprite.Group()
        self.player_list = pygame.sprite.Group()
        self.player = player

        # Background image
        self.background = None

        # How far this world has been scrolled left/right
        self.world_shift = 0

    # Update everythign on this level
    def update(self):
        """ Update everything in this level."""
        self.platform_list.update()
        self.enemy_list.update()

    def draw(self, screen):
        """ Draw everything on this level. """

        # Draw the background
        screen.fill(BLUE)

        # Draw all the sprite lists that we have
        self.platform_list.draw(screen)
        self.enemy_list.draw(screen)

    def shift_world(self, shift_x):
        """ When the user moves left/right and we need to scroll
        everything: """

        # Keep track of the shift amount
        self.world_shift += shift_x

        # Go through all the sprite lists and shift
        for platform in self.platform_list:
            platform.rect.x += shift_x

        for enemy in self.enemy_list:
            enemy.rect.x += shift_x

        for player in self.player_list:
            if player != self.player:

                player.rect.x += shift_x

# Create platforms for the level

class multi_level(Level):
    def __init__(self, player, tileData):

        # Call the parent constructor
        Level.__init__(self, player)

        # Array with width, height, x, and y of platform
        tiles = tileData
        #Each block is 32/32 pixels
        # Go through the array above and add platforms
        for row_num, row in enumerate(tiles):
            for tile_num,tile in enumerate(row):
                if tile == 1:
                    block = Wall(SCREEN_WIDTH/25, SCREEN_HEIGHT/25)
                    block.rect.x = (tile_num)*(SCREEN_WIDTH/25)
                    block.rect.y = (row_num)*(SCREEN_HEIGHT/25)
                    block.player = self.player
                    self.platform_list.add(block)
                if tile == 2:
                    block = Platform(SCREEN_WIDTH/25, SCREEN_HEIGHT/25)
                    block.rect.x = (tile_num)*(SCREEN_WIDTH/25)
                    block.rect.y = (row_num)*(SCREEN_HEIGHT/25)
                    block.player = self.player
                    self.platform_list.add(block)



class Level_01(Level):
    """ Definition for level 1. """

    def __init__(self, player):
        """ Create level 1. """

        # Call the parent constructor
        Level.__init__(self, player)

        # Array with width, height, x, and y of platform
        tiles = [[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,2,2,2,2,2,2,2,2,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,2,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,2,2,2],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,2,2,2,2,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,2,2,1,2,2,2,2,2,2],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
                 [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]

        ]

        #Each block is 32/32 pixels
        # Go through the array above and add platforms
        for row_num, row in enumerate(tiles):
            for tile_num,tile in enumerate(row):
                if tile == 1:
                    block = Wall(SCREEN_WIDTH/25, SCREEN_HEIGHT/25)
                    block.rect.x = (tile_num)*(SCREEN_WIDTH/25)
                    block.rect.y = (row_num)*(SCREEN_HEIGHT/25)
                    block.player = self.player
                    self.platform_list.add(block)
                if tile == 2:
                    block = Platform(SCREEN_WIDTH/25, SCREEN_HEIGHT/25)
                    block.rect.x = (tile_num)*(SCREEN_WIDTH/25)
                    block.rect.y = (row_num)*(SCREEN_HEIGHT/25)
                    block.player = self.player
                    self.platform_list.add(block)
        #for platform in level:
        #    block = Platform(platform[0], platform[1])
        #    block.rect.x = platform[2]
        #    block.rect.y = platform[3]
        #    block.player = self.player
        #    self.platform_list.add(block)
#We send the pos on a player movement update, along with a unique id.
def sendPOS(player):
    playerInfo = {'type':"playerInfo",'username':player.username, 'x-pos': player.rect.x - player.level.world_shift, 'y-pos': player.rect.y, 'color': player.color}
    data_to_send = pickle.dumps(playerInfo)
    sock.send(bytes(data_to_send))


def startMultiplayer(list_of_players, active_sprite_list):
    #This will be threaded to allow for multiplayer incoming messages to be recieved without blocking main game thread.

    threading.Thread(target=mainMultiplayerLoop,args=(list_of_players, active_sprite_list)).start()

def getLevelFromServer(player):

    serverRequest  = {'type':"level"}
    data_to_send = pickle.dumps(serverRequest)
    sock.send(bytes(data_to_send))
    data = sock.recv(2048) # get response with level data
    loadedData = pickle.loads(data)
    Level = multi_level(player, loadedData["level"])

    return Level


def mainMultiplayerLoop(list_of_players, active_sprite_list):
    #sock.bind(("127.0.0.1", 5005))
    while True:
        data = sock.recv(1024) # buffer size is 1024 bytes
        loadedData = pickle.loads(data)
        flag = True
        #check if it's a player we already are drawing.
        for player in list_of_players:

            if loadedData['username'] == player.username:

                flag = False
                player.rect.x = loadedData['x-pos'] + list_of_players[0].level.world_shift
                player.rect.y = loadedData['y-pos']
                break
        if flag:

            player = Player(loadedData['username'], loadedData['color'])
            player.level = list_of_players[0].level
            player.rect.x = loadedData['x-pos'] + list_of_players[0].level.world_shift
            player.rect.y = loadedData['y-pos']
            nameTag = Nametag(player)
            active_sprite_list.add(player)
            active_sprite_list.add(nameTag)
            list_of_players[0].level.player_list.add(player)
            list_of_players.append(player)

def main():
    """ Main Program """
    pygame.init()


    # Set the height and width of the screen
    size = [SCREEN_WIDTH, SCREEN_HEIGHT]
    screen = pygame.display.set_mode(size)

    pygame.display.set_caption("Multi Test")

    # Create the player
    player = Player("Justin", RED)

    #At this point we need to get the level from our server.
    level = getLevelFromServer(player)


    # Create all the levels
    level_list = []
    level_list.append(level)
    list_of_players = []
    # Set the current level
    current_level_no = 0
    current_level = level_list[current_level_no]
    active_sprite_list = pygame.sprite.Group()
    player.level = current_level

    player.rect.x = 340
    player.rect.y = SCREEN_HEIGHT - player.rect.height
    nameTag = Nametag(player)
    active_sprite_list.add(player)
    active_sprite_list.add(nameTag)
    list_of_players = [player]
    startMultiplayer(list_of_players, active_sprite_list)
    # Loop until the user clicks the close button.
    done = False

    # Used to manage how fast the screen updates
    clock = pygame.time.Clock()

    # -------- Main Program Loop -----------
    previousX = 0
    previousY = 0
    previousShift = 0
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    player.go_left()
                if event.key == pygame.K_RIGHT:
                    player.go_right()
                if event.key == pygame.K_UP:
                    player.jump()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT and player.change_x < 0:
                    player.stop()
                if event.key == pygame.K_RIGHT and player.change_x > 0:
                    player.stop()

        # Update the player.
        active_sprite_list.update()


        # Update items in the level
        current_level.update()


        # If the player gets near the right side, shift the world left (-x)
        if player.rect.right > (SCREEN_WIDTH/2)+1:
            diff = player.rect.right - (SCREEN_WIDTH/2)+1
            player.rect.right = (SCREEN_WIDTH/2)+1
            current_level.shift_world(-diff)



        # If the player gets near the left side, shift the world right (+x)
        if player.rect.left < (SCREEN_WIDTH/2)-20:
            diff = ((SCREEN_WIDTH/2)-20) - player.rect.left
            player.rect.left = (SCREEN_WIDTH/2)-20
            current_level.shift_world(diff)

        if previousX != player.rect.x or previousY != player.rect.y or player.level.world_shift != previousShift:
            sendPOS(player)
        previousX = player.rect.x
        previousY = player.rect.y
        previousShift = player.level.world_shift
        #Send player location to server

        # ALL CODE TO DRAW SHOULD GO BELOW THIS COMMENT
        current_level.draw(screen)
        active_sprite_list.draw(screen)

        # ALL CODE TO DRAW SHOULD GO ABOVE THIS COMMENT

        # Limit to 60 frames per second
        clock.tick(60)

        # Go ahead and update the screen with what we've drawn.
        pygame.display.flip()

    # Be IDLE friendly. If you forget this line, the program will 'hang'
    # on exit.
    pygame.quit()

if __name__ == "__main__":
    main()
