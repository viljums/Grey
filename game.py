# air time resets sword cd.
import tmx, time
import pygame


class Game (object):
    def main (self, screen):
        clock = pygame.time.Clock ()

        background = pygame.image.load ('background.png')
        
        self.jump = pygame.mixer.Sound('jump.wav')
        self.shoot = pygame.mixer.Sound ('shoot.wav')
        self.explosion = pygame.mixer.Sound ('explosion.wav')

        sprites = ScrolledGroup()
        sprites.camera_x = 0

        self.tilemap = tmx.load ('map.tmx', screen.get_size())

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
            screen.blit (background, (0, 0))
            self.tilemap.draw(screen)
            pygame.display.flip()

            if self.player.is_dead:
                print 'YOU DIED'
                return

    

class Player (pygame.sprite.Sprite):

    def __init__ (self, location, *groups):
        super (Player, self).__init__(*groups)
        self.image = pygame.image.load('player.png')
        self.stand = self.image
        self.leftImage = pygame.image.load ('player-right.png')
        self.rect = pygame.rect.Rect (location, self.image.get_size())
        self.resting = False
        self.dy = 0
        self.is_dead = False
        self.direction = 1
        self.gun_cooldown = 0
        self.walkAnim = None
        self.walkLib = []
        for x in range (1, 7):
            currentImage = pygame.image.load ('PlayerImages/walk%s.png' % x) 
            self.walkLib.append (currentImage)

    def walkAnimation (self, currentTime):
            currentTime = (currentTime % 0.5) + 0.1
            currentTime = round (currentTime, 1)
            currentImage = None

            for imageNumber in range (6):
                frameTime = imageNumber/10.0
                if currentTime >= frameTime: 
                    currentImage = self.walkLib[imageNumber]
            return currentImage


    def update(self, dt, game, currentTime):
        last = self.rect.copy()
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT]:
            self.rect.x -= 300 * dt
            self.direction = -1
            if self.resting:
                self.image = pygame.transform.flip (self.walkAnimation (currentTime), True, False)
        elif key[pygame.K_RIGHT]:
            self.rect.x += 300 * dt
            self.direction = 1
            if self.resting:
                self.image = self.walkAnimation (currentTime)
        else:
            currentTime = 0
            if self.direction < 0:
                self.image = pygame.transform.flip (self.stand, True, False)
            elif self.direction > 0:
                self.image = self.stand



        self.gun_cooldown = max (0, self.gun_cooldown - dt) 
        
        if self.resting and key[pygame.K_SPACE]:
            game.jump.play()
            self.dy = -500
        self.dy = min (400, self.dy + 40)
        self.rect.y += self.dy * dt

        new = self.rect
        self.resting = False
        for cell in game.tilemap.layers['triggers'].collide(new, 'blockers'):
            blockers = cell['blockers']
            if 'l' in blockers and last.right <= cell.left and new.right > cell.left:
                new.right = cell.left
            if 'r' in blockers and last.left >= cell.right and new.left < cell.right:
                new.left = cell.right
            if 't' in blockers and last.bottom <= cell.top and new.bottom > cell.top:
                self.resting = True
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

class Bullet (pygame.sprite.Sprite):
    image = pygame.image.load('bullet.png')
    def __init__(self, location, direction, *groups):
        super(Bullet, self).__init__(*groups)
        self.rect = pygame.rect.Rect(location, self.image.get_size())
        self.direction = direction
        self.lifespan = 1

    def update (self, dt, game, currentTime):
        self.lifespan -= dt
        if self.lifespan < 0:
            self.kill()
            return
        self.rect.x += self.direction * 400 * dt

        

class Sword (pygame.sprite.Sprite):

    def __init__(self, *groups):
        super(Sword, self).__init__(*groups)
        self.rightImage = pygame.image.load('PlayerImages/sword.png')
        self.image = self.rightImage 
        self.leftImage = pygame.transform.flip (self.image, True, False)
        self.standartRect = pygame.rect.Rect ((0,0), self.image.get_size())
        self.rect = self.standartRect
        self.nextFrame = -1
        self.animStart = 0
        self.slash = False
        self.slashLib = []

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

        if key[pygame.K_LSHIFT]:
            self.slash = True
            animStart = time.time ()
        if self.slash:
            if  time.time () - self.animStart> 0.05:
                self.nextFrame += 1
                self.animStart = time.time ()
            if self.nextFrame == 4:
                self.nextFrame = -1
                self.animStart = 0
                self.slash = False
                self.image = self.leftImage

            self.updateSlashLib (game)
            self.image, self.rect = self.slashLib[self.nextFrame]




            if pygame.sprite.spritecollide(self, game.enemies, True):
                    game.explosion.play()
                
        
    def updateSlashLib (self, game):
        #slash lib conf 
        rotSword1 = (pygame.transform.rotate (self.image, -45),
                game.player.rect.move (-64, -32))
        rotSword2 = (pygame.transform.rotate (self.image, -90),
                game.player.rect.move (0, -64))
        rotSword3 = (pygame.transform.rotate (self.image, -140),
                game.player.rect.move (32, -64))
        rotSword4 = (self.leftImage, game.player.rect.move (32, 32))
        self.slashLib = [rotSword1, rotSword2, rotSword3, rotSword4]
        
        if game.player.direction < 0:
            rotSword1 = (pygame.transform.rotate (self.image, 45), 
                game.player.rect.move (32, -32))
            rotSword2 = (pygame.transform.rotate (self.image, 90),
                game.player.rect.move (32, -64))
            rotSword3 = (pygame.transform.rotate (self.image, 140),
                game.player.rect.move (-64, -64))
            rotSword4 = (self.rightImage, game.player.rect.move (-64, 32))

        self.slashLib = [rotSword1, rotSword2, rotSword3, rotSword4]

if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode ((640, 480))
    Game().main(screen)

