import time, tmx
import pygame
from pygame.locals import*

class Game (object):
    def __init__ (self):
        self.changeLevel = False
        self.sprites = tmx.SpriteLayer()
        self.mapLib = ['Maps/protomap.tmx', 'Maps/layer2.tmx']
        self.mapNumber = 0
        self.mapFile = self.mapLib[self.mapNumber]
        self.tilemap = tmx.load (self.mapFile, screen.get_size())
        start_cell = self.tilemap.layers['triggers'].find('player')[0]
        self.player = Player((start_cell.px, start_cell.py), self.sprites)
        self.sword = Sword (self.sprites)
        self.cdBar = CDBar (self.sprites)

    def main (self, screen):
        clock = pygame.time.Clock ()

        self.jump = pygame.mixer.Sound('jump.wav')
        self.explosion = pygame.mixer.Sound ('explosion.wav')

        sprites = ScrolledGroup()
        sprites.camera_x = 0

        self.mapFile = self.mapLib[self.mapNumber]
        self.tilemap = tmx.load (self.mapFile, screen.get_size())

        #self.sprites = tmx.SpriteLayer()




        self.tilemap.layers.append (self.sprites)



        self.enemies = tmx.SpriteLayer()
        self.immortalSprites = tmx.SpriteLayer ()
        for enemy in self.tilemap.layers['triggers'].find('enemy'):
            enemyType = enemy['enemy']
            if 'worm' in enemyType:
                Worm ((enemy.px, enemy.py), self.enemies)
            elif 'spitter' in enemyType:
                Spitter ((enemy.px, enemy.py), self.enemies)
            else:
                Enemy ((enemy.px, enemy.py), self.enemies)

        for cell in self.tilemap.layers['triggers'].find('blockers'):
            blocker = cell['blockers']
            if 'crawler' in blocker:
                Crawler (pygame.Rect (cell.px, cell.py, cell.width, cell.height), self.enemies)
            
        self.tilemap.layers.append(self.enemies)
        self.tilemap.layers.append (self.immortalSprites)


        image_x = 323
        image_y = 369


        while True:
            dt = clock.tick(30)
            for event in pygame.event.get ():
                if event.type == pygame.QUIT:
                    return 'dead'
                if event.type == pygame.KEYDOWN and \
                        event.key == pygame.K_ESCAPE:
                    return 'dead'
                self.player.get_event (event)

            self.tilemap.update (dt / 1000., self) #mechanix
            screen.fill ((255, 255, 255))
            self.tilemap.draw(screen)
            pygame.display.flip()

            if self.player.is_dead:
                return 'dead'
            if self.changeLevel:
                self.changeLevel = False
                return 'next'

    def nextMap (self, screen):
        self.mapNumber += 1
        self.main(screen)



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
        self.airJump = False

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

        self.firstJump = False 
        self.secondJump = False
        self.keyUp = False
        self.air = False
        
        self.rotation = 0
        self.spinAttack = False

    def get_event (self, event):
        if event.type == KEYDOWN:
            if event.key == K_SPACE and self.grounded and not self.air:
                self.firstJump = True
                self.grounded = False
            elif event.key == K_SPACE and (self.keyUp or self.air) and self.airJump: 
                self.secondJump = True
                self.airJump = False
        if event.type == KEYUP:
            if event.key == K_SPACE:
                self.keyUp = True
                self.firstJump = False


    def update(self, dt, game):
        last = self.walkingAnimation (dt)
        self.slashAnimation (game)
        self.jump (game)
        self.jumpAnimation (dt)
        self.spin (game)
        self.spriteBlock (game, last)
        self.spikes (game)



    def walkingAnimation (self, dt):
        last = self.rect.copy()
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT]:
            self.rect.x -= 300 * dt
            self.direction = -1
            self.stand = self.leftStand
            if self.air:
                self.rect.x -= 100 * dt # speed boost while in air
            if self.grounded:
                self.image = self.animation.getReverse (0.05, False)
        elif key[pygame.K_RIGHT]:
            self.rect.x += 300 * dt
            self.direction = 1
            self.stand = self.rightStand
            if self.air:
                self.rect.x += 100 * dt
            if self.grounded:
                self.image = self.animation.getNextFrame (0.05, False)
        else:
            if self.direction < 0:
                self.image = pygame.transform.flip (self.rightStand, True, False)
                self.image = self.leftStand
            elif self.direction > 0:
                self.image = self.rightStand
        return last

        #animation when slashing

    def slashAnimation (self, game):

        if game.sword.slash: 
            nextFrame = None
            if game.sword.animDir > 0: 
                nextFrame = self.slashAnim.getNextFrame (0.05)
            else:
                nextFrame = self.slashAnim.getReverse (0.05)

            if nextFrame != 'end':
                self.image = nextFrame

    def jump (self, game):
        if self.firstJump or self.secondJump: 
            self.dy -= 150
            
            if self.firstJump and self.dy < -2000:
                self.firstJump = False
            if self.secondJump and self.dy < -400:
                self.secondJump = False
                self.airJump = False
                self.rotation = 0

                self.spinAttack = True
            
            #resets sword cd
            game.sword.interval = 0

        #jumpimage
    def jumpAnimation (self, dt):
        jumpImage = pygame.image.load ('PlayerImages/jump0.png')
        if self.dy < 0 and self.direction > 0:
                self.image =  jumpImage
        elif self.dy < 0 and self.direction < 0:
                self.image = pygame.transform.flip (jumpImage, True, False)
        #gravity


        self.dy = min (400, self.dy + 40) # 400
        self.rect.y += self.dy * dt

        #spin
    def spin (self, game):
        if self.spinAttack:
            if self.direction > 0:
                #rotation
                self.rotation -= 30
                rotImage = pygame.image.load ('PlayerImages/rotjump.png')
                self.image = pygame.transform.rotate (rotImage, self.rotation)
       
            elif self.direction < 0:
                self.rotation -= 30
                rotImage = pygame.image.load ('PlayerImages/rotjump.png')
                rotImage = pygame.transform.rotate (rotImage, self.rotation)
                self.image = pygame.transform.flip (rotImage, True, False)

            if pygame.sprite.spritecollide(self, game.enemies, True):
                    game.explosion.play()

            
        #blocking the sprite
    def spriteBlock (self, game, last):
        self.air = True # checks if player is flying through air
        new = self.rect
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
                self.firstJump = False
                self.secondJump = False
                self.keyUp = False
                self.airJump = True
                self.air = False
                self.spinAttack = False
                self.spinAttackOffset = time.time () # player remains lethal for a few decasecs on ground

            if 'b' in blockers and last.top >= cell.bottom and new.top < cell.bottom:
                new.top = cell.bottom
                self.dy = 0
                self.secondJump = False
        game.tilemap.set_focus(new.x, new.y)

        self.groups()[0].camera_x = self.rect.x - 320

    def spikes (self, game):
        if game.tilemap.layers['triggers'].collide (self.rect, 'spikes'):
            game.player.is_dead = True

    def playSound (self, game):
        if self.firstJump or self.secondJump: 

            game.jump.play ()

        


class ScrolledGroup(pygame.sprite.Group):
    def draw(self, surface):
        for sprite in self.sprites():
            surface.blit(sprite.image, (sprite.rect.x - self.camera_x, sprite.rect.y))

class Enemy(pygame.sprite.Sprite):
    image = pygame.image.load('Enemies/enemy.png')
    def __init__(self, location, *groups):
        super(Enemy, self).__init__(*groups)
        self.rect = pygame.rect.Rect (location, self.image.get_size())
        self.direction = 1

    def update (self, dt, game):
        self.rect.x += self.direction * 100 * dt
        for cell in game.tilemap.layers['triggers'].collide(self.rect, 'reverse'):
            if self.direction > 0:
                self.rect.right = cell.left
            else:
                self.rect.left = cell.right
            self.direction *= -1
            break
        if self.rect.colliderect(game.player.rect) and not game.player.spinAttack:
            game.player.is_dead = True

class Worm (pygame.sprite.Sprite):
    def __init__(self, location, *groups):
        super(Worm, self).__init__(*groups)
        self.image = pygame.image.load('Enemies/worm0.png')
        self.rect = pygame.rect.Rect (location, self.image.get_size())
        self.direction = 1
        wormLib = []
        for imgNumber in range (4):
            currentImage = pygame.image.load ('Enemies/worm%s.png' % imgNumber)
            wormLib.append (currentImage)

        self.anim = Animation (wormLib)

    def update (self, dt, game):
        self.rect.x += self.direction * 100 * dt
        if self.direction > 0:
            self.image = self.anim.getNextFrame (0.1, False) 
        else:
            self.image = self.anim.getReverse (0.1, False)

        for cell in game.tilemap.layers['triggers'].collide(self.rect, 'reverse'):
            if self.direction > 0:
                self.rect.right = cell.left

            else:
                self.rect.left = cell.right
            self.direction *= -1
            break
        if self.rect.colliderect(game.player.rect) and not game.player.spinAttack:
            game.player.is_dead = True
       
class Spitter (pygame.sprite.Sprite):
    def __init__(self, location, *groups):
        super(Spitter, self).__init__(*groups)
        self.image = pygame.image.load('Enemies/spitter.png')
        self.rect = pygame.rect.Rect (location, self.image.get_size())
        self.location = location
        self.direction = 1
        self.shootStart = time.time ()
        spitLib = []
        for imgNumber in range (4):
            currentImage = pygame.image.load ('Enemies/spitterSpit%s.png' % imgNumber)
            spitLib.append (currentImage)
        for imgNumber in range (-3, 1):
            currentImage = pygame.image.load ('Enemies/spitterSpit%s.png' % (- imgNumber))
            spitLib.append (currentImage)

        self.anim = Animation (spitLib)
        self.spitSide = self.rect.topleft

    def spittingAnim (self, game):
        nextFrame = self.anim.getNextFrame (0.05)
        if nextFrame == 'end':
            self.shootStart = time.time ()
            Spit (self.spitSide, self.direction, game.immortalSprites)
            self.image = pygame.image.load('Enemies/spitter.png')
        else:
            self.image = nextFrame


    def update (self, dt, game):
        self.rect.x += self.direction * 50 * dt
        if self.direction > 0:
            self.spitSide = self.rect.midright
        else:
            self.spitSide = self.rect.midleft

        for cell in game.tilemap.layers['triggers'].collide(self.rect, 'reverse'):
            if self.direction > 0:
                self.rect.right = cell.left
            else:
                self.rect.left = cell.right
            self.direction *= -1
            break
        if self.rect.colliderect(game.player.rect) and not game.player.spinAttack:
            game.player.is_dead = True

        if not self.anim.timer (self.shootStart, 2):
            self.spittingAnim (game)



class Spit (pygame.sprite.Sprite):
    image = pygame.image.load ('Enemies/spit.png')
    def __init__(self, location, direction, *groups): 
        super(Spit, self).__init__(*groups)
        self.rect = pygame.rect.Rect (location, self.image.get_size())
        self.direction = direction
        self.anim = Animation ([])
        self.lifeTime = time.time ()
        self.rotation = 0

    def update (self, dt, game):
        self.rotation += 90
        self.image = pygame.transform.rotate (self.image, 90)
        self.lifeTime = time.time ()
        self.rect.x += self.direction * 130 * dt
        if not self.anim.timer (self.lifeTime, 2):
            self.kill ()

        
        if self.rect.colliderect(game.player.rect) and not game.player.spinAttack:
            game.player.is_dead = True


class Crawler (pygame.sprite.Sprite):
    def __init__(self, patrolRect, *groups): 
        super(Crawler, self).__init__(*groups)
        self.image = pygame.image.load ('Enemies/crawler.png')
        self.rect = pygame.rect.Rect (patrolRect.topleft, self.image.get_size())
        self.patrolRect = patrolRect
        self.rect.bottomright = self.patrolRect.topleft

    def getDirection (self):
        rect = self.rect
        path = self.patrolRect
        if rect.right == path.left and rect.bottom == path.top:
            self.direction = 'right'
        elif rect.left == path.right and rect.bottom == path.top:
            self.direction = 'down'
        if rect.left == path.right and rect.top == path.bottom:
            self.direction = 'left'
        elif rect.right == path.left and rect.top == path.bottom:
            self.direction = 'up'

    def update (self, dt, game):
        self.getDirection ()
        print self.direction

        if self.direction == 'right':
            self.rect.left += 100 * dt
            self.rect.left = min (self.rect.left, self.patrolRect.right)
        elif self.direction == 'down':
            self.rect.top += 100 *dt
            self.rect.top = min (self.rect.top, self.patrolRect.bottom)
        elif self.direction == 'left':
            self.rect.right -= 100 * dt
            self.rect.right = max (self.rect.right, self.patrolRect.left)
        elif self.direction == 'up':
            self.rect.bottom -= 100 * dt
            self.rect.bottom = max (self.rect.bottom, self.patrolRect.top)

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
        self.interval = 0

        # transforming sprites to make animation frames

        rotSword1 = pygame.transform.rotate (self.image, -45)
        rotSword2 = pygame.transform.rotate (self.image, -90)
        rotSword3 = pygame.transform.rotate (self.image, -145)
        rotSword4 = self.leftImage
        rotSword5 = self.leftImage

        slashLib = [rotSword1, rotSword2, rotSword3, rotSword4, rotSword5]

        self.animation = Animation (slashLib)

    def update (self, dt, game):
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
                

        if key[pygame.K_LSHIFT] and not self.coolDown and not game.player.spinAttack:
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
                
        
        if game.player.spinAttack:
            self.image = pygame.image.load ('PlayerImages/blank.png')

        if game.tilemap.layers['triggers'].collide(self.rect, 'nextLevel'):
            game.changeLevel = True
        
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

        
class CDBar (pygame.sprite.Sprite):
    def __init__(self, *groups):
        super(CDBar, self).__init__(*groups)
        self.image = pygame.image.load ('PlayerImages/blank.png')
        self.rect = pygame.rect.Rect ((0, 0), self.image.get_size())

    def update (self, dt, game):
        x, y, w, h = game.player.rect
        w = 8; y -= 16; h = 30
        slashTime = game.sword.interval
        if slashTime != 0:
            h -= (10 *(time.time () - slashTime))
        else:
            h = 0
        barSurf = pygame.Surface ((h, w))
        barSurf.fill ((0, 0, 0))
        self.rect = pygame.Rect (x, y, w, h)
        self.image = barSurf
        


class Animation (object):

    def __init__ (self, animLib):
        self.animLib = animLib
        self.frame = -1
        self.animStart = 0.
        

    #gets False if interval in cd hadnt reached.

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
    game = Game()
    status = game.main(screen)
    while True:
        if status == 'next':
            status = game.nextMap (screen)
        elif status == 'dead':
            print "Player is kill"
            break
        elif status == 'victory':
            print "Is Victorious"
            break
        else:
            print "error"
            break
