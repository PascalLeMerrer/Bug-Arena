# coding: utf-8

class HomeLayer(Layer):
    ''' the game menu '''
    is_event_handler = True     #: enable pyglet's events

    def __init__( self ):

        super(HomeLayer, self).__init__()

        self.text_title = pyglet.text.Label("Play",
            font_size=32,
            x=director.get_window_size()[0] /2,
            y=director.get_window_size()[1] / 2,
            anchor_x='center',
            anchor_y='center' )

    def draw( self ):
        self.text_title.draw()

    def on_key_press( self, k , m ):
        if k == key.ENTER:
            director.replace(RotoZoomTransition(
                        (scene_list[1] ),
                        1.25)
                    )
            return True