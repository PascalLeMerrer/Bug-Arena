#
# cocos2d
# http://cocos2d.org
#
import random

from cocos.director import director
from cocos.layer import Layer, ColorLayer
from cocos.scene import Scene
from cocos.scenes.transitions import RotoZoomTransition
from cocos.actions import RotateBy, MoveBy, Repeat, Reverse
from cocos.sprite import Sprite
from cocos import collision_model
from cocos import euclid

import pyglet
from pyglet.window import key


class HomeLayer(Layer):
    ''' Game menu. '''

    is_event_handler = True     # Enable pyglet's events

    def __init__(self):
        super(HomeLayer, self).__init__()
        window_size = director.get_window_size()
        self.text_title = pyglet.text.Label("Play",
            font_size=32,
            x=window_size[0] / 2,
            y=window_size[1] / 2,
            anchor_x='center',
            anchor_y='center')

    def draw(self):
        self.text_title.draw()

    def on_key_press(self, k, m):
        if k == key.ENTER:
            director.replace(RotoZoomTransition((gameScene), 1.25))
            return True
        else:
            return False


class Bug(Sprite):
    ''' Characters to be destroyed. '''

    def __init__(self):
        self.duration = random.randint(2, 8)
        bugSpriteSheet = pyglet.resource.image('SpriteSheet.png')
        bugGrid = pyglet.image.ImageGrid(bugSpriteSheet, 2, 3)
        animation_period = max(self.duration / 100, 0.05)  # seconds

        animation = bugGrid.get_animation(animation_period)
        super(Bug, self).__init__(animation)

        screen_height = director.get_window_size()[1]

        self.scale = 0.5
        rect = self.get_rect()

        self.speed = (screen_height + rect.height) / self.duration
        self.cshape = collision_model.AARectShape(
            euclid.Vector2(rect.center[0], rect.center[1]),
                           rect.width / 2, rect.height / 2)

    def start(self):
        ''' places the bug to its start position
            duration: the time in second for the
            bug to go to the bottom of the screen '''
        self.spawn()

        wasColliding = self.respawnOnCollision()
        while wasColliding:
            wasColliding = self.respawnOnCollision()

        self.rotation = -self.duration
        rotate = RotateBy(self.duration * 2, 1)
        self.do(Repeat(rotate + Reverse(rotate)))

        rect = self.get_rect()
        self.cshape.center = euclid.Vector2(rect.center[0], rect.center[1])

    def spawn(self):
        ''' pops at a random place on top of the screen '''
        rect = self.get_rect()
        half_width = rect.width / 2
        screen_width, screen_height = director.get_window_size()
        spawnX = random.randint(half_width, screen_width - half_width)
        self.position = (spawnX, screen_height + rect.height / 2)
        self.updateCshapePosition()

    def respawnOnCollision(self):
        ''' if the bug is colliding with another one,
            redraw it at another random place on top of screen
            returns True when it was colliding
        '''
        wasColliding = False
        for other in active_bug_list:
            if bugLayer.collision_manager.they_collide(self, other):
                self.spawn()
                wasColliding = True
                break
        return wasColliding

    def moveBy(self, dx, dy):
        ''' moves the bug
            dx distance in pixels along horizontal axis
            dy distance in pixels along vertical axis '''
        self.position = (self.position[0] + dx, self.position[1] + dy)
        self.updateCshapePosition()

    def updateCshapePosition(self):
        self.cshape.center.x, self.cshape.center.y = self.position


class BugLayer(Layer):
    ''' Layer on which the bugs walk. '''

    is_event_handler = True     # Enable pyglet's events.

    def __init__(self):
        super(BugLayer, self).__init__()
        self.schedule_interval(createBug, 1)  # Creates a bug every 3 seconds

        cell_width = 100    # ~ bug image width * 1,25
        cell_height = 190   # ~bug image height * 1.25
        screen_width = director.get_window_size()[0]
        screen_height = director.get_window_size()[1]
        self.collision_manager = collision_model.CollisionManagerGrid(
                                                        0.0, screen_width,
                                                        0.0, screen_height,
                                                        cell_width,
                                                        cell_height)
        self.schedule(update, update)

    def on_mouse_press(self, x, y, buttons, modifiers):
        ''' invoked when the mouse button is pressed
            x, y the coordinates of the clicked point
        '''
        mouse_x, mouse_y = director.get_virtual_coordinates(x, y)

        for bug in self.collision_manager.objs_touching_point(mouse_x,
                                                              mouse_y):
            self.collision_manager.remove_tricky(bug)
            active_bug_list.remove(bug)
            bug.stop()
            bugLayer.remove(bug)
            bug_pool.append(bug)


def update(dt, *args, **kwargs):
    ''' Updates the bugs position
        kills them when they are going out of the screen.
        invoked at each frame '''
    bugLayer.collision_manager.clear()
    for bug in active_bug_list:
        bugLayer.collision_manager.add(bug)

    for bug in active_bug_list:
        dy = bug.speed * dt / bug.duration
        if dy < 0.2:
            dy = 0.2
        can_move = True
        for other in bugLayer.collision_manager.iter_colliding(bug):
            if bug.get_rect().top >= other.get_rect().top:
                can_move = False    # blocked by a colliding bug

        if can_move:
            bug.moveBy(0, -dy)
            if bug.position[1] < 0:
                active_bug_list.remove(bug)
                bug.stop()
                bugLayer.collision_manager.remove_tricky(bug)
                bugLayer.remove(bug)
                bug_pool.append(bug)


def createBug(dt, *args, **kwargs):
    ''' Get a bug instance from the pool or
        creates one when the pool is empty. '''
    if len(bug_pool):
        bug = bug_pool.pop(random.randint(0, len(bug_pool) - 1))
    else:
        bug = Bug()
    bugLayer.add(bug)
    bugLayer.collision_manager.add(bug)
    bug.start()
    active_bug_list.append(bug)


if __name__ == "__main__":

    pyglet.resource.path = ['images', 'sounds', 'fonts']
    pyglet.resource.reindex()

    director.init(resizable=True)
    director.window.set_fullscreen(True)

    active_bug_list = []
    bug_pool = []
    for i in range(50):
        bug_pool.append(Bug())

    homeLayer = HomeLayer()
    colorLayer1 = ColorLayer(0, 255, 255, 255)
    homeScene = Scene(colorLayer1, homeLayer)

    bugLayer = BugLayer()
    colorLayer2 = ColorLayer(128, 16, 16, 255)
    gameScene = Scene(bugLayer)

    director.run(homeScene)
