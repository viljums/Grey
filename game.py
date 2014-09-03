import tmx, time
import pygame


class Game (object):
    def main (self, screen):
        clock = pygame.time.Clock ()

        self.jump = pygame.mixer.Sound('jump.wav')
        self.explosion = pygame.mixer.Sound ('explosion.wav')

        sprites = ScrolledGroup()
        sprites.camera_x = 0

        self.tilemap = tmx.load ('protomap.tmx', screen.get_size())

        self.sprites = tmx.SpriteLayer()
        start_cell = self.tilemap.layers['triggers'].find('player')[0]
        self.player = Player((start_cell.px, start_cell.py), self.sprites)

        self.sword = Sword (self.sprites)

        self.tilemap.layers.append (self.sprites)


        self.enemies = tmx.SpriteLayer()
        for enemy in self.tilemap.layers['triggers'].find('enemy'):
            Enemy ((enemy.px, enemy.py), self.enemies)
        self.tilemap.layers.append(self.enemies)


        image_x = 323
        image_y = 369

        currentTime = 0

        while True:
            dt = clock.tick(30)
            currentTime = time.time () + dt
            for event in pygame.event.get ():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN and \
                        event.key == pygame.K_ESCAPE:
                    return

            self.tilemap.update (dt / 1000., self, currentTime) #mechanix
            screen.fill ((255, 255, 255))
            self.tilemap.draw(screen)
            pygame.display.flip()

            if self.player.is_dead:
                print 'YOU DIED'
                return


class Player (pygame.sprite.Sprite):

    def __init__ (self, location, *groups):
        super (Player, self).__init__(*groups)
        self.rightStand = pygame.image.load('player.png')
        self.leftStand = pygame.transform.flip (self.rightStand, True, False)
        self.stand = self.rightStand
        self.image = self.rightStand

        self.rect = pygame.rect.Rect (location, self.image.get_size())
        self.grounded = False
        self.dy = 0
        self.is_dead = False
        self.direction = 1
        self.walkAnim = None
        self.walkLib = []
        self.slashLib = []
        self.animDir = None
        self.jumpNumber = 0

        slashLib = []
        walkLib = []
        for x in range (4):
            currentImage = pygame.image.load ('PlayerImages/sla%s.png' % x)
            slashLib.append (currentImage)
        slashLib.append (self.rightStand)

        for x in range (1, 7):
            currentImage = pygame.image.load ('PlayerImages/walk%s.png' % x) 
            walkLib.append (currentImage)

        self.animation = Animation (walkLib)
        self.slashAnim = Animation (slashLib)

        self.jumpNumber = 0
        self.jumpStart = 0


    def update(self, dt, game, currentTime):
        last = self.rect.copy()
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT]:
            self.rect.x -= 300 * dt
            self.direction = -1
            self.stand = self.leftStand
            if self.grounded:
                self.image = self.animation.getReverse (0.05, False)
        elif key[pygame.K_RIGHT]:
            self.rect.x += 300 * dt
            self.direction = 1
            self.stand = self.rightStand
            if self.grounded:
                self.image = self.animation.getNextFrame (0.05, False)
        else:
            currentTime = 0
            if self.direction < 0:
                self.image = pygame.transform.flip (self.rightStand, True, False)
                self.image = self.leftStand
            elif self.direction > 0:
                self.image = self.rightStand

        #animation when slashing

        if game.sword.slash:
            nextFrame = None
            if game.sword.animDir > 0: 
                nextFrame = self.slashAnim.getNextFrame (0.05)
            else:
                nextFrame = self.slashAnim.getReverse (0.05)

            if nextFrame != 'end':
                self.image = nextFrame


        if self.grounded and key[pygame.K_SPACE] and not self.animation.timer (self.jumpStart, 0.3):
            game.jump.play()
            self.dy = -500
            game.sword.interval = 0

            self.jumpNumber += 1
            self.jumpStart = time.time ()

            # double jump

        self.dy = min (400, self.dy + 40)
        self.rect.y += self.dy * dt

        new = self.rect
        if self.jumpNumber == 2:
            self.grounded = False
            self.jumpNumber = 0
            self.jumpStart = 0

        for cell in game.tilemap.layers['triggers'].collide(new, 'blockers'):
            blockers = cell['blockers']
            if 'l' in blockers and last.right <= cell.left and new.right > cell.left:
                new.right = cell.left
            if 'r' in blockers and last.left >= cell.right and new.left < cell.right:
                new.left = cell.right
            if 't' in blockers and last.bottom <= cell.top and new.bottom > cell.top:
                self.grounded = True
                new.bottom = cell.top
                self.dy = 0
            if 'b' in blockers and last.top >= cell.bottom and new.top < cell.bottom:
                new.top = cell.bottom
                self.dy = 0
        
        game.tilemap.set_focus(new.x, new.y)

        self.groups()[0].camera_x = self.rect.x - 320

        


class ScrolledGroup(pygame.sprite.Group):
    def draw(self, surface):
        for sprite in self.sprites():
            surface.blit(sprite.image, (sprite.rect.x - self.camera_x, sprite.rect.y))

class Enemy(pygame.sprite.Sprite):
    image = pygame.image.load('enemy.png')
    def __init__(self, location, *groups):
        super(Enemy, self).__init__(*groups)
        self.rect = pygame.rect.Rect (location, self.image.get_size())
        self.direction = 1

    def update (self, dt, game, currentTime):
        self.rect.x += self.direction * 100 * dt
        for cell in game.tilemap.layers['triggers'].collide(self.rect, 'reverse'):
            if self.direction > 0:
                self.rect.right = cell.left
            else:
                self.rect.left = cell.right
            self.direction *= -1
            break
        if self.rect.colliderect(game.player.rect):
            game.player.is_dead = True

        

class Sword (pygame.sprite.Sprite):

    def __init__(self, *groups):
        super(Sword, self).__init__(*groups)
        self.rightImage = pygame.image.load('PlayerImages/sword.png')
        self.leftImage = pygame.transform.flip (self.rightImage, True, False)
        self.image = self.rightImage 
        self.standartRect = pygame.rect.Rect ((0,0), self.image.get_size())
        self.rect = self.standartRect
        self.slash = False
        self.rectLib = []
        self.animDir = None
        self.coolDown = False

        # transforming sprites to make animation frames

        rotSword1 = pygame.transform.rotate (self.image, -45)
        rotSword2 = pygame.transform.rotate (self.image, -90)
        rotSword3 = pygame.transform.rotate (self.image, -145)
        rotSword4 = self.leftImage
        rotSword5 = self.leftImage

        slashLib = [rotSword1, rotSword2, rotSword3, rotSword4, rotSword5]

        self.animation = Animation (slashLib)

    def update (self, dt, game, currentTime):
        slash = False
        self.rect = self.standartRect
        if game.player.direction < 0 and not slash:
            self.rect.topleft = game.player.rect.midright
            self.image = self.leftImage
        elif game.player.direction > 0 and not slash:
            self.image = self.rightImage
            self.rect.topright = game.player.rect.midleft

        key = pygame.key.get_pressed()

        #animation
        if self.coolDown:
            self.coolDown = self.animation.timer (self.interval, 3) 
        else:
            self.interval = 0 
                

        if key[pygame.K_LSHIFT] and not self.coolDown:
            self.slash = True
            animStart = time.time ()
            self.animDir = game.player.direction
            self.coolDown = True
            self.interval = time.time ()
            

        if self.slash:
            self.updateSlashLib (game)
            if self.animDir > 0:
                nextFrame = self.animation.getNextFrame (0.05) 
            elif self.animDir < 0:
                nextFrame = self.animation.getReverse (0.05)
            self.rect = self.animation.rectAnimator(0.05, self.slashRectLib)
            if nextFrame == 'end':
                self.slash = False
                self.rect = self.standartRect
            else:
                self.image = nextFrame

            if pygame.sprite.spritecollide(self, game.enemies, True):
                    game.explosion.play()
                
        
        
    def updateSlashLib (self, game):
        #slash lib conf, relies on direction 

        rotSword1 = game.player.rect.move (-64, -32)
        rotSword2 = game.player.rect.move (0, -64)
        rotSword3 = game.player.rect.move (22, -55)
        rotSword4 = game.player.rect.move (32, 32)
        rotSword5 = game.player.rect.move (32, 32)

        self.slashRectLib = [rotSword1, rotSword2, rotSword3, rotSword4, rotSword5]
        if self.animDir < 0:
            rotSword1 = game.player.rect.move (32, -32)
            rotSword2 = game.player.rect.move (0, -64)
            rotSword3 = game.player.rect.move (-54, -54)
            rotSword4 = game.player.rect.move (-64, 32)
            rotSword5 = game.player.rect.move (-64, 32)

        self.slashRectLib = [rotSword1, rotSword2, rotSword3, rotSword4, rotSword5]


class Animation (object):

    def __init__ (self, animLib):
        self.animLib = animLib
        self.frame = -1
        self.animStart = 0.
        

    def timer (self, start, cd):
        if time.time () - start > cd:
            return False
        else:
            return True

    def getNextFrame (self, frameTime, stopAfter = True):
        if not self.timer (self.animStart, frameTime):
                self.frame += 1
                self.animStart = time.time ()

        if self.frame == len (self.animLib) and stopAfter:
                self.animStart = 0
                self.frame = -1
                return 'end'
        elif self.frame == len (self.animLib):
                self.animStart = 0
                self.frame = -1

                
        return self.animLib[self.frame]

        

    def rectAnimator (self, frameTime, rectLib):
        if self.frame == len (rectLib) and stopAfter:
                return 'end'

        return rectLib [self.frame]

    def getReverse (self, frameTime, stopAfter = True):
        surface = self.getNextFrame (frameTime, stopAfter)
        if surface != 'end':
            return pygame.transform.flip (surface, True, False)
        else:
            return 'end'


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode ((640, 480))
    Game().main(screen)

