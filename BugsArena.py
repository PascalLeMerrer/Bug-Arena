# coding: utf-8
""" Bug Tracker main file """
# cocos2d
# http://cocos2d.org
#

# todo
# gérer la trajectoire des cafards pour qu'ils se contournent


import random
import math
import sys
from cocos.director import director
from cocos.layer import Layer, ColorLayer
from cocos.scene import Scene
from cocos.scenes.transitions import RotoZoomTransition
from cocos.actions import MoveBy, MoveTo, RotateBy, Repeat, Reverse
from cocos.sprite import Sprite
# from cocos.audio.effect import Effect
from cocos.cocosnode import CocosNode
from cocos import collision_model
from cocos import euclid

import pyglet
from pyglet.window import key
# from pyglet.media import ManagedSoundPlayer
from cshape import OrientableRectShape

class HomeLayer(Layer):
    ''' Game menu. '''

    is_event_handler = True     # Enable pyglet's events

    def __init__(self):
        super(HomeLayer, self).__init__()
        screen_width, screen_height = director.get_window_size()
        self.text_title = pyglet.text.Label("Jouer",
            font_size=32,
            x = screen_width / 2,
            y = screen_height / 2,
            anchor_x='center',
            anchor_y='center')

    def draw(self):
        self.text_title.draw()

    def on_key_press(self, key_code, modifiers):
        """ invoked when the user presses a keyboard key """
        if key_code == key.ENTER:
            director.replace(NotifiyingTransition(GAME_SCENE, GAME_MODEL.start))
            # SOUND_MANAGER.buzz_sound.play()
            return True
        else:
            return False

class BugLayer(Layer):
    ''' Layer on which the bugs walk. '''

    is_event_handler = True     # Enable pyglet's events.

    def __init__(self, player):
        super(BugLayer, self).__init__()
        self.player = player

        cell_width = 100    # ~ bug image width * 1,25
        cell_height = 190   # ~bug image height * 1.25
        screen_width, screen_height = director.get_window_size()
        self.collision_manager = collision_model.CollisionManagerGrid(
                                                        0.0, screen_width,
                                                        0.0, screen_height,
                                                        cell_width,
                                                        cell_height)

    def on_mouse_press(self, point_x, point_y, buttons, modifiers):
        ''' invoked when the mouse button is pressed
            x, y the coordinates of the clicked point
        '''
        mouse_x, mouse_y = director.get_virtual_coordinates(point_x, point_y)

        for bug in self.collision_manager.objs_touching_point(mouse_x,
                                                              mouse_y):
            self.shake()
            self.player.add_points(bug.value)
            kill_bug(bug)

    def on_key_press(self, key_code, modifiers):
        """ invoked when a keyboard key is pressed 
            see CocosNode """
        if key_code == key.ESCAPE:
            director.replace(RotoZoomTransition((HOME_SCENE), 1.25))
            # SOUND_MANAGER.buzz_sound.play()
            return True
        else:
            return False

    def shake(self):
        shake_part = MoveBy((0.0, -3.0), 0.1)
        shake = shake_part + Reverse(shake_part)*2 + shake_part
        self.do(shake)

    def remove_all(self):
        ''' removes all children from this layer '''
        bugs = self.get_children()
        for bug in bugs:
            self.remove(bug)


class HudLayer(Layer):
    ''' Head Up Display. '''

    def __init__(self, player):
        super(HudLayer, self).__init__()
        screen_width, screen_height = director.get_window_size()
        self.player = player
        self.score_label = pyglet.text.Label("score",
                                             font_size=15,
                                             x = 10,
                                             y = screen_height - 20)
        self.life_label = pyglet.text.Label("vie",
                                             font_size=15,
                                             x = screen_width - 200,
                                             y = screen_height - 20)
        self.previous_life = player.MAX_LIFE

        self._create_lifebar(player.MAX_LIFE)

    def draw(self):
        self.score_label.text = "score : " + str(self.player.score)
        self.score_label.draw()
        self.life_label.draw()
        if self.player.life != self.previous_life:
            self.previous_life = self.player.life
            self._create_lifebar(self.player.life)

    def _create_lifebar(self, value):
        """ creates a new lifebar if the player life is superior to 0
            Parameters:
                value: ther player's life points
        """
        if hasattr(self, "lifebar"):
            self.lifebar.kill()
        
        if value > 0:
            self.lifebar = ColorLayer(0, 255, 0, 255, value, 20)
            screen_width, screen_height = director.get_window_size()
            self.lifebar.position = (screen_width - 160, screen_height - 25)
        
        if value < 20:
            self.lifebar.color = (255, 0, 0)
        elif value < 50:
            self.lifebar.color = (255, 80, 0)

        self.add(self.lifebar)


class GameOverLayer(Layer):
    ''' End of game screen. '''

    is_event_handler = True     # Enable pyglet's events

    def __init__(self):
        super(GameOverLayer, self).__init__()
        screen_width, screen_height = director.get_window_size()
        half_width = screen_width / 2
        half_height = screen_height / 2
        self.text_title = pyglet.text.Label("Vous avez perdu.",
            font_size=32,
            x = half_width,
            y = 100 + half_height,
            anchor_x='center',
            anchor_y='center')
        self.score_label = pyglet.text.Label("Votre score: 0",
            font_size=24,
            x = half_width,
            y = half_height,
            anchor_x='center',
            anchor_y='center')
        self.text_continue = pyglet.text.Label("Nouvelle partie",
            font_size=24,
            x = half_width,
            y = half_height - 100,
            anchor_x='center',
            anchor_y='center')

    def draw(self):
        self.text_title.draw()
        self.score_label.text = "Votre score : " + str(PLAYER.score)
        self.score_label.draw()
        self.text_continue.draw()

    def on_key_press(self, key_code, modifiers):
        """ invoked when the user presses a keyboard key """
        if key_code == key.ENTER:
            director.replace(NotifiyingTransition(GAME_SCENE, GAME_MODEL.start))
            # SOUND_MANAGER.buzz_sound.play()
            return True
        else:
            return False


class Player(object):
    """ the human player """

    def __init__(self):
        self.MAX_LIFE = 100
        self.LIFE_POINT_PER_BUG = 50
        self.reset()

    def reset(self):
        ''' turns player to its initial state: full life, no points'''
        self.score = 0
        self.life = self.MAX_LIFE

    def add_points(self, points):
        """ increase player score
            points: the  number of points to add to the score
        """
        self.score += points
        print 'actuated > score= ', self.score

    def remove_life_points(self):
        """ decrease player life points, if it is positive 
        """
        if self.life >= self.LIFE_POINT_PER_BUG:
            self.life -= self.LIFE_POINT_PER_BUG
        else:
            self.life = 0
        if self.life == 0:
            print 'before stop > score= ', self.score
            GAME_MODEL.stop()
            BUG_LAYER.remove_all()
            director.replace(RotoZoomTransition(GAME_OVER_SCENE, 1.25))


class Bug(Sprite):

    ''' Characters to be destroyed. '''
    def __init__(self):
        self.duration = random.randint(2, 8)
        if(self.duration < 5):
            self.value = 1000   
            image = 'bug1-small.png'
        else:
            self.value = 500
            image = 'bug2-small.png'

        bug_sprite_sheet = pyglet.resource.image(image)
        bug_grid = pyglet.image.ImageGrid(bug_sprite_sheet, 1, 6)
        animation_period = max(self.duration / 100, 0.05)  # seconds

        animation = bug_grid.get_animation(animation_period)
        super(Bug, self).__init__(animation)

        screen_height = director.get_window_size()[1]

        rect = self.get_rect()

        self.speed = (screen_height + rect.height) / self.duration
        self.cshape = OrientableRectShape(
            euclid.Vector2(rect.center[0], rect.center[1]),
                           rect.width / 2, rect.height / 2, 0)
        self.is_colliding = False

    def start(self):
        ''' places the bug to its start position
            duration: the time in second for the
            bug to go to the bottom of the screen '''
        self.spawn()

        self.is_colliding = self.respawn_on_collision()
        collision_counter = 1 if self.is_colliding else 0
        while self.is_colliding:
            self.is_colliding = self.respawn_on_collision()
            if self.is_colliding:
                collision_counter += 1
            if collision_counter > 3:
                break

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
        spawn_x = random.randint(half_width, screen_width - half_width)
        self.position = (spawn_x, screen_height + rect.height / 2)
        self.cshape.center.x, self.cshape.center.y = self.position
        self.cshape.update_position()
        self.cshape.rotate(self.rotation)

    def respawn_on_collision(self):
        ''' if the bug is colliding with another one,
            redraw it at another random place on top of screen
            returns True when it was colliding
        '''
        is_colliding = False
        for other in GAME_MODEL.active_bug_list:
            if BUG_LAYER.collision_manager.they_collide(self, other):
                self.spawn()
                is_colliding = True
                break
        return is_colliding

    def move_by(self, delta_x, delta_y):
        ''' moves the bug
            delta_x distance in pixels along horizontal axis
            delta_y distance in pixels along vertical axis '''
        self.position = (self.position[0] + delta_x, self.position[1] + delta_y)
        self.cshape.center.x, self.cshape.center.y = self.position
        self.cshape.update_position()
        self.cshape.rotate(self.rotation)


def cb_update(delta_t, *args, **kwargs):
    ''' Updates the bugs position
        kills them when they are going out of the screen, 
        and decrease player life points
        invoked at each frame
        delta_t: time elapsed since previous call '''
    BUG_LAYER.collision_manager.clear()
    for bug in GAME_MODEL.active_bug_list:
        BUG_LAYER.collision_manager.add(bug)

    screen_width = director.get_window_size()[0]

    for bug in GAME_MODEL.active_bug_list:
        delta_y = bug.speed * delta_t / bug.duration
        if delta_y < 0.2:
            delta_y = 0.2
        can_move = True
        for other in BUG_LAYER.collision_manager.iter_colliding(bug):
            if bug.get_rect().top >= other.get_rect().top:
                can_move = False    # blocked by a colliding bug

        if can_move:
            if bug.rotation > 180:
                rotation = bug.rotation - 360
            else:
                rotation = bug.rotation

            delta_x = - delta_y * math.sin(rotation)
            if bug.x - bug.width < 0 and delta_x < 0:
                delta_x = 0
            elif bug.x + bug.width > screen_width and delta_x > 0:
                delta_x = 0

            bug.move_by(delta_x, -delta_y)
            
            if bug.position[1] < 0:
                PLAYER.remove_life_points()
                kill_bug(bug)


class SoundManager(object):
    """ handle sound effects of the game """
    def __init__(self):
        director.init(audio_backend='sdl')
        self.buzz_sound = pyglet.resource.media(
                            'Beehive-Dylan_Hi-2147.wav', streaming=False)
        # self.buzz_sound.eos_action = ManagedSoundPlayer.EOS_LOOP 

class GameModel(CocosNode):
    def __init__(self):
        super(GameModel, self).__init__()
        self.active_bug_list = []
        self.bug_pool = []
        for i in range(50):
            self.bug_pool.append(Bug())

    def activate_bug(self):
        ''' Get a bug instance from the pool or
            creates one when the pool is empty.
            Then add it to the game '''
        if len(self.bug_pool):
            bug = self.bug_pool.pop(random.randint(0, len(self.bug_pool) - 1))
        else:
            bug = Bug()
        bug.start()
        self.active_bug_list.append(bug)
        return bug

    def deactivate_bug(self, bug):
        ''' puts a bug out of the game '''
        bug.stop()
        self.active_bug_list.remove(bug)
        self.bug_pool.append(bug)
        
    def deactivate_all(self):
        for bug in self.active_bug_list:
            self.deactivate_bug(bug)

    def start(self):
        ''' starts the game'''
        self.deactivate_all()
        self.schedule_interval(cb_create_bug, 1)  # Creates a bug every second
        self.schedule(cb_update)
        self.resume_scheduler()
        PLAYER.reset()

    def stop(self):
        ''' stops the game '''
        self.pause_scheduler()
        self.unschedule(cb_create_bug)
        self.unschedule(cb_update)


def cb_create_bug(delta_t, *args, **kwargs):
    ''' Get a bug instance from the pool or
        creates one when the pool is empty. 
        delta_t is the time elapsed since previous call'''
    bug  = GAME_MODEL.activate_bug()
    BUG_LAYER.add(bug)
    BUG_LAYER.collision_manager.add(bug)
    if bug.is_colliding:
        kill_bug(bug) # the bug did not find any free place to spawn

def kill_bug(bug):
    """ removes a bug from the game scene"""
    GAME_MODEL.deactivate_bug(bug)
    try:
        BUG_LAYER.collision_manager.remove_tricky(bug)
    except KeyError:
        pass
    try:
        BUG_LAYER.remove(bug)
    except Exception:
        pass

class NotifiyingTransition(RotoZoomTransition):
    '''A RotoZoomTransition with an end notification'''
    def __init__(self, destination, exit_callback):
        """ destination: the target Scene
            exit_callback: is invoked at the end of the transition, when the game is ready """
        super(NotifiyingTransition, self).__init__(destination, 1.25)
        self.exit_callback = exit_callback

    def on_exit(self):
        super(NotifiyingTransition, self).on_exit()
        self.exit_callback()


if __name__ == "__main__":
    
    FULLSCREEN = False

    for arg in sys.argv:
        if arg == 'fullscreen': 
            FULLSCREEN = True

    pyglet.resource.path = ['images', 'sounds', 'fonts']
    pyglet.resource.reindex()
    # SOUND_MANAGER = SoundManager()

    director.init(resizable = not FULLSCREEN)
    director.window.set_fullscreen(FULLSCREEN)

    GAME_MODEL = GameModel()
    HOME_LAYER = HomeLayer()
    COLOR_LAYER = ColorLayer(128, 16, 16, 255)
    HOME_SCENE = Scene(COLOR_LAYER, HOME_LAYER)
    PLAYER = Player()
    BUG_LAYER = BugLayer(PLAYER)
    HUD_LAYER = HudLayer(PLAYER)
    GAME_SCENE = Scene(BUG_LAYER, HUD_LAYER)
    GAME_OVER_LAYER = GameOverLayer()
    GAME_OVER_SCENE = Scene(COLOR_LAYER, GAME_OVER_LAYER)

    director.run(HOME_SCENE)