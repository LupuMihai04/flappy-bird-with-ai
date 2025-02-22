import pygame
import neat
import os
import random
import pickle

pygame.font.init()

WIN_WIDTH = 600
WIN_HEIGHT = 800
FLOOR = 730
STAT_FONT = pygame.font.SysFont("comicsans", 50)
END_FONT = pygame.font.SysFont("comicsans", 70)
DRAW_LINES = False


WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")).convert_alpha())
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")).convert_alpha())
BG_IMG = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "bg.png")).convert_alpha(), (600, 900))

gen = 0

class Bird: # Bird class representing the flappy bird
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y): # Initialize the object
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self): # make the bird jump
        self.vel =  -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self): # make the bird move
        self.tick_count += 1

        d = self.vel*self.tick_count + 1.5*self.tick_count**2

        # terminal velocity
        if d >= 16:
            d = 16

        if d < 0:
            d -= 2

        self.y = self.y + d

        if d < 0 or self.y < self.height + 50: # tilt the bird up
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else: # tilt the bird down
            if self.tilt >-90:
                self.tilt -= self.ROT_VEL

    def draw(self, win): # draw the bird
        self.img_count += 1

        # looping through the images to create the animation of the bird
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*4 +1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # animation does not exist if the bird is diving
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        # tilt the bird
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Pipe: # Pipe class representing the pipe object
    GAP = 200
    VEL = 5

    def __init__(self, x): # initialize pipe object
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0

        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    def set_height(self): # set the height of the pipe, from the top of the screen
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self): # move pipe based on velocity
        self.x -= self.VEL

    def draw(self, win): # draw the top and the bottom of the pipe
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird): # returns if a point is colliding with a point of the pipe
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
           return True

        return False

class Base: # Base class representing the moving floor of the game
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y): # initialize the floor
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self): # move the floor, looking like its scrolling
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win): # draw the floor as two images that move in circular motion
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))



def draw_window(win, birds, pipes, base, score, gen, pipe_ind): # draws the windows for the main game loop
    if gen == 0:
        gen = 1

    win.blit(BG_IMG, (0,0))

    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)
    for bird in birds:
        if DRAW_LINES: # draw lines from the bird to both pipes
            try:
                pygame.draw.line(win, (255, 0, 0),
                                 (bird.x + bird.img.get_width() / 2, bird.y + bird.img.get_height() / 2),
                                 (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width() / 2, pipes[pipe_ind].height),
                                 5)
                pygame.draw.line(win, (255, 0, 0),
                                 (bird.x + bird.img.get_width() / 2, bird.y + bird.img.get_height() / 2),
                                 (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width() / 2,pipes[pipe_ind].bottom),
                                 5)
            except:
                pass

        bird.draw(win) # draw bird

    score_label = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10)) # score

    score_label = STAT_FONT.render("Gens: " + str(gen - 1), 1, (255, 255, 255))
    win.blit(score_label, (10, 10)) # generations

    score_label = STAT_FONT.render("Alive: " + str(len(birds)), 1, (255, 255, 255))
    win.blit(score_label, (10, 50)) # birds still alive

    pygame.display.update()

def main(genomes, config): # runs the simulation of the current population of birds and sets their fitness according to the distance they reach in the game
    global WIN, gen
    win = WIN
    gen += 1

    nets = [] # networks associated with the genome
    ge = [] # genome
    birds = [] # birds that use the networks to play

    for genome_id, g in genomes:
        g.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230,350))
        ge.append(g)


    base = Base(FLOOR)
    pipes = [Pipe(700)]
    score = 0

    clock = pygame.time.Clock()

    run = True
    while run and len(birds) > 0:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
              run = False
              pygame.quit()
              quit()

        pipe_ind = 0
        if len(birds) > 0: # determine whether to use the first or second pipe on the screen for the neural network input
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1


        for x, bird in enumerate(birds): # give each bird a fitness of 0.1 for each frame it stays alive
            bird.move()
            ge[x].fitness += 0.1

            # send bird location, top pipe location and bottom pipe location and determine from network whether to jump or not
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5: # we use a tanh activation function so result will be between -1 and 1. if over 0.5 jump
                bird.jump()

        base.move()

        add_pipe = False
        rem = []

        for pipe in pipes:
            pipe.move()

            for x, bird in enumerate(birds):
                if pipe.collide(bird): # check for collisions
                   ge[x].fitness -= 1
                   birds.pop(x)
                   nets.pop(x)
                   ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                   pipe.passed = True
                   add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(WIN_WIDTH))

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < -50:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)


        base.move()
        draw_window(WIN, birds, pipes, base, score, gen, pipe_ind)

        if score > 20: # break if score gets large enough saving the best performing bird
            with open("best_bird.pickle", "wb") as f:
                pickle.dump(nets[0], f)
            break

def best_network(config):

    global WIN

    # load the trained neural network
    with open("best_bird.pickle", "rb") as f:
        best_net = pickle.load(f)

    bird = Bird(230, 350)
    base = Base(FLOOR)
    pipes = [Pipe(700)]
    score = 0
    win = WIN
    clock = pygame.time.Clock()

    run = True
    while run:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(pipes) > 1 and bird.x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
            pipe_ind = 1

        # use the trained neural network to make a decision
        output = best_net.activate((bird.y, abs(bird.y - pipes[pipe_ind].height),
                                    abs(bird.y - pipes[pipe_ind].bottom)))

        if output[0] > 0.5:  # if the output is greater than 0.5, jump
            bird.jump()

        bird.move()
        base.move()

        rem = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()
            if pipe.collide(bird): # check for collision
                run = False

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

        if add_pipe:
            score += 1
            pipes.append(Pipe(WIN_WIDTH))

        for r in rem:
            pipes.remove(r)

        if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < -50: # stop if bird falls out of bounds
            run = False

        draw_window(WIN, [bird], pipes, base, score, 0, pipe_ind)  # Draw the game screen

def run(config_path): # runs the NEAT algorithm to train a neural network to play Flappy Bird
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)

    p = neat.Population(config)  # create the population, which is the top-level object for a NEAT run

    # add a stdout reporter to show progress in the terminal
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main, 50) # run for up to 50 generations

    print('\nBest genome:\n{!s}'.format(winner)) # show final stats

if __name__ == "__main__": # determine path to configuration file
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")

    run(config_path) # for training the best neural network

    #best_network(config_path) # for running the saved best neural network