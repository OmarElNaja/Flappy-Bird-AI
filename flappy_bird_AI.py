import pygame
import neat
import random
import os
import time
pygame.font.init()

WINDOW_HEIGHT = 800
WINDOW_WIDTH = 500
GEN = 0 #Keeps track of generation number
BIRD_IMAGES = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 50) #Font for drawing score and generation number

class Bird:
    IMAGES = BIRD_IMAGES
    MAX_ROTATION = 25
    ROTATION_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tickCount = 0
        self.velocity = 0
        self.height = self.y
        self.imageCount = 0
        self.image = self.IMAGES[0]

    def jump(self):
        self.velocity = -10.5 #negative velocity is upwards, positive is downwards
        self.tickCount = 0
        self.height = self.y

    def move(self):
        self.tickCount += 1

        displacement = self.velocity*self.tickCount + 1.5*self.tickCount**2 #formula for displacement

        #Limit downward movement to 16 pixels
        if displacement >= 16:
            displacement = 16

        #Move up 2 more pixels when moving upwards
        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        # Tilt the bird upwards or downwards depending on the direction it's moving in
        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROTATION_VEL

    def draw(self, win):
        self.imageCount += 1

        # Animations of bird flapping wings
        if self.imageCount < self.ANIMATION_TIME:
            self.image = self.IMAGES[0]
        elif self.imageCount < 2*self.ANIMATION_TIME:
            self.image = self.IMAGES[1]
        elif self.imageCount < 3*self.ANIMATION_TIME:
            self.image = self.IMAGES[2]
        elif self.imageCount < 4*self.ANIMATION_TIME:
            self.image = self.IMAGES[1]
        elif self.imageCount < 4*self.ANIMATION_TIME + 1:
            self.image = self.IMAGES[0]
            self.imageCount = 0

        # If bird is moving downwards, don't flap wings
        if self.tilt <= -80:
            self.image = self.IMAGES[1]
            self.imageCount = self.ANIMATION_TIME*2 # image count still increases despite same image for multiple frames

        # Rotate the bird
        rotatedImage = pygame.transform.rotate(self.image, self.tilt)
        newRectangle = rotatedImage.get_rect(center=self.image.get_rect(topleft = (self.x, self.y)).center) # Rotate around center rather than top left of image
        win.blit(rotatedImage, newRectangle.topleft) # draw rotated image onto window

    # Function for object collisions
    def get_mask(self):
        return pygame.mask.from_surface(self.image)

class Pipe:
    GAP = 200 #space between pipes
    VEL = 5 #pipes move backwards, bird stays still

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMAGE, False, True) #top pipe (bottom pipe image flipped)
        self.PIPE_BOTTOM = PIPE_IMAGE #bottom pipe
        self.passed = False #keeps track of if bird has passed a pipe
        self.set_height()

    #Randomly sets the height of both the top and bottom pipe
    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    #Moves pipe to the left when called
    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top)) #top pipe
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom)) #bottom pipe

    #Checks for collisions between bird and bottom or top pipe
    def collide(self, bird):
        birdMask = bird.get_mask()
        topMask = pygame.mask.from_surface(self.PIPE_TOP) #Mask for top pipe
        bottomMask = pygame.mask.from_surface(self.PIPE_BOTTOM) #Mask for bottom pipe

        topOffset = (self.x - bird.x, self.top - round(bird.y)) #distance between top pipe's mask and bird's mask
        botOffset = (self.x - bird.x, self.bottom - round(bird.y)) #distance between bottom pipe's mask and bird's mask

        #Returns first point of overlap between bird mask and bottom pipe / top pipe respectively
        #If no overlap found, returns None
        botCollisionPoint = birdMask.overlap(bottomMask, botOffset)
        topCollisionPoint = birdMask.overlap(topMask, topOffset)

        if botCollisionPoint or topCollisionPoint:
            return True

        return False

class Base:
    VEL = 5
    WIDTH = BASE_IMAGE.get_width()
    IMAGE = BASE_IMAGE

    def __init__(self, y):
        self.y = y
        self.x1 = 0 #One base image is at x = 0
        self.x2 = self.WIDTH #The other base image is to the right of the first one (off the screen)

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        #If first base image moves off the screen (to the left), shift it to the right
        #of the second base image
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        #If second base image moves off the screen (to the left), shift it to the right
        #of the first base image
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMAGE, (self.x1, self.y))
        win.blit(self.IMAGE, (self.x2, self.y))

def draw_window(win, birds, pipes, base, score, gen):
    win.blit(BG_IMAGE, (0,0)) #draw background image

    for pipe in pipes:
        pipe.draw(win)

    #Draw score in white
    text = STAT_FONT.render("Score: " + str(score), 1, (255,255,255))
    win.blit(text, (WINDOW_WIDTH - 10 - text.get_width(), 10))

    #Draw generarion number in white
    text = STAT_FONT.render("Gen: " + str(gen), 1, (255,255,255))
    win.blit(text, (10, 10))

    base.draw(win)

    for bird in birds:
        bird.draw(win)

    pygame.display.update()

def main(genomes, config):
    global GEN
    GEN += 1
    neural_nets = [] #List of neural networks corresponding to each bird
    ge = [] #List of genomes corresponding to each bird
    birds = [] #List of Birds in the generation

    for _, genome in genomes:
        network = neat.nn.FeedForwardNetwork.create(genome, config)
        neural_nets.append(network)
        birds.append(Bird(230, 350))
        genome.fitness = 0 #Initializing the fitness score for the bird
        ge.append(genome)


    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    score = 0 #Game score (how many pipes passed)

    runGame = True

    while runGame:
        clock.tick(60) # Do a max of 60 ticks per second to remove the dependence of the game's speed on the computer it's running on
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                runGame = False
                pygame.quit()
                quit()

        #Decides which pipe to use for the inputs to a bird's neural network, if there are 2 pipes on the screen.
        #If the bird has not passed the first pipe, use that for the inputs.
        #If it has, use the second pipe for the inputs.
        #If there are no birds left in the population, end the current generation and start over
        pipeInd = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipeInd = 1
        else:
            runGame = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            neuralNetOutput = neural_nets[x].activate((bird.y, abs(bird.y - pipes[pipeInd].height), abs(bird.y - pipes[pipeInd].bottom)))
            if neuralNetOutput[0] > 0.5:
                bird.jump()

        addPipe = False
        removed_pipes = []
        for pipe in pipes:
            for x, bird in enumerate(birds):
                #If a bird collides with a pipe, remove it from the birds, NN and genomes list and
                #reduce its fitness score
                if pipe.collide(bird):
                    ge[x].fitness -= 1
                    birds.pop(x)
                    neural_nets.pop(x)
                    ge.pop(x)

                #If a pipe passes the bird, set flags to generate a new pipe
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    addPipe = True

            #If pipe is off the screen, remove it from the list of pipes
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                removed_pipes.append(pipe)

            pipe.move()

        #If a pipe passes the bird, add 1 to score and generate a new pipe
        if addPipe:
            score += 1
            for g in ge:
                g.fitness += 5 #Increment fitness scores of any birds still alive
            pipes.append(Pipe(600))

        #Remove pipes that have moved off the screen
        for rem in removed_pipes:
            pipes.remove(rem)

        for x, bird in enumerate(birds):
            #If bird collides with floor or goes too high, remove it from the birds, NN and genomes list
            if bird.y + bird.image.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                neural_nets.pop(x)
                ge.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score, GEN)

def run(configPath):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, configPath) #Returns the config file

    population = neat.Population(config)

    #Generate statistics for the generation in terminal
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    #main is the fitness function
    winner = population.run(main,50)

#Find the path to config.txt (which contains configurations for NEAT algorithm)
#and pass it into run
if __name__ == "__main__":
    localDir = os.path.dirname(__file__)
    configPath = os.path.join(localDir, "config.txt")
    run(configPath)
