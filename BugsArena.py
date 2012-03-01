# coding: utf-8
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
#from cocos import collision_manager

#import cocos.euclid

import pyglet
#from pyglet import gl, font
#from pyglet.image import Animation

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
        self.duration = random.randint(2, 10);
        bugSpriteSheet = pyglet.resource.image('SpriteSheet.png')
        bugGrid = pyglet.image.ImageGrid(bugSpriteSheet, 2, 3)
        animation_period = max(self.duration/100, 0.05)  # seconds
        
        animation = bugGrid.get_animation(animation_period)
        super(Bug, self).__init__(animation)
        

        #rect = self.get_rect()
        #self.cshape = collision_manager.AARectShape(
        #    euclid.Vector2(center_x, center_y),
        #    rect.width / 2, rect.height / 2)

    def start(self):
        ''' places the bug to its start position
            duration: the time in second for the
            bug to go to the bottom of the screen '''
        spawnX = director.get_window_size()[0] * random.random()
        screen_width = director.get_window_size()[0]

        # TODO: optimize to avoid multiple calculations
        rect = self.get_rect()
        half_width = rect.width / 2
        if(spawnX < half_width):
            spawnX = half_width
        elif spawnX > screen_width - half_width:
            spawnX = screen_width - half_width

        screenHeight = director.get_window_size()[1]
        self.position = (spawnX, screenHeight + rect.height/2)
        self.rotation = -self.duration
        rotate = RotateBy(self.duration*2, 1)

        move = MoveBy((0, -screenHeight - self.get_rect().height), self.duration)
        self.do(move | Repeat(rotate + Reverse(rotate)))
        self.schedule_interval(checkBugPosition, 1, self)

    def stop(self):
        ''' Stops the moving and the position checking. '''
        Sprite.stop(self)
        self.unschedule(checkBugPosition)


class BugLayer(Layer):
    ''' Layer on which the bugs walk. '''

    is_event_handler = True     # Enable pyglet's events.

    def __init__(self):
        super(BugLayer, self).__init__()
        self.schedule_interval(createBug, 1)  # Creates a bug every 3 seconds

        #global collision_manager
        #collision_manager = Coll

    def on_mouse_press(self, x, y, buttons, modifiers):
       #global collision_manager
       #for actor in collision_manager.objs_touching_point(x, y):
       #    if isinstance(actor, Bug):
       #        actor.kill()
        for bug in active_bug_list:
            if bug.contains(x, y):
                active_bug_list.remove(bug)
                bug.stop()
                bugLayer.remove(bug)
                bug_pool.append(bug)


def checkBugPosition(dt, *args, **kwargs):
    ''' Kill the bug when outside of screen. '''
    bug = args[0]
    if bug.position[1] < 0:
        active_bug_list.remove(bug)
        bug.stop()
        bugLayer.remove(bug)
        bug_pool.append(bug)


def createBug(dt, *args, **kwargs):
    ''' Get a bug instance from the pool or
        creates one when the pool is empty. '''
    if len(bug_pool):
        bug = bug_pool.pop(random.randint(0, len(bug_pool)-1))
    else:
        bug = Bug()
    bugLayer.add(bug)

    bug.start()
    active_bug_list.append(bug)

    #global collision_manager
    #collision_manager.add(bug)


if __name__ == "__main__":

    pyglet.resource.path = ['images', 'sounds', 'fonts']
    pyglet.resource.reindex()

    director.init(resizable=True)
    #director.window.set_fullscreen(True)

    active_bug_list = []
    bug_pool = []
    for i in range(50):
        bug_pool.append(Bug())

    homeLayer = HomeLayer()
    colorLayer1 = ColorLayer(0, 255, 255, 255)
    homeScene = Scene(colorLayer1, homeLayer)

    bugLayer = BugLayer()
    colorLayer2 = ColorLayer(128, 16, 16, 255)
    gameScene = Scene(colorLayer2, bugLayer)

    director.run(homeScene)
