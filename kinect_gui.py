# TODO
#  - Have a look at freenect async data getters.
#  - Ensure Kinect tilt is neutral at startup.

from freenect import sync_get_depth as get_depth, sync_get_video as get_video
import numpy

import pygtk
pygtk.require('2.0')
import gtk

import gobject

import cairo

import time
import math


class Kinect(object):

    def __init__(self):
        self._loaded_rgb = None
        self._loaded_depth = None

        self.latest_rgb = None
        self.latest_depth = None
        self.latest_present = False

    def depth_to_cm(self, depth):
        if depth == 2047:
            return -1

        # Formula from http://vvvv.org/forum/the-kinect-thread.
        return math.tan(depth / 1024.0 + 0.5) * 33.825 + 5.7

    def get_frames(self):

        found_kinect = False
        try:
            # Try to obtain Kinect images.
            (depth, _), (rgb, _) = get_depth(), get_video()
            found_kinect = True
        except TypeError:
            # Use local data files.
            if self._loaded_rgb == None:
                self._loaded_rgb = \
                        numpy.load('2012-03-02_14-36-48_rgb.npy')
            rgb = self._loaded_rgb

            if self._loaded_depth == None:
                self._loaded_depth = \
                        numpy.load('2012-03-02_14-36-48_depth.npy')
            depth = self._loaded_depth

        # Memorize results.
        self.latest_rgb = rgb
        self.latest_depth = depth
        self.latest_present = found_kinect

        return found_kinect, rgb, depth


class DepthAnalyser(object):

    KINECT_DEPTH_NAN = 2047

    def __init__(self, depth):
        self._depth = depth

    def find_sticks(self):

        STICK_THRESHOLD = 30

        # Normalize to 0 - 255, in particular
        # deal with Kinect NAN value.
        depth = self._depth
        i = numpy.amin(depth)
        depth_clean = numpy.where(depth == self.KINECT_DEPTH_NAN, 0, depth)
        a = numpy.amax(depth_clean)
        depth255 = numpy.where(depth == self.KINECT_DEPTH_NAN,
                0, 255 - (depth - i) * 254.0 / (a - i))

        # Remove further objects.
        depth_near = numpy.where(depth255 > 255 - STICK_THRESHOLD, 1, 0)

        # Look for first stick (on the left).
        ya, xa = numpy.nonzero(depth_near[:, :320])
        x = numpy.amin(xa)
        y = numpy.amin(ya)
        w = numpy.amax(xa) - x
        h = numpy.amax(ya) - y
        left = x, y, w, h

        # Look for second stick (on the right).
        ya, xa = numpy.nonzero(depth_near[:, 320:])
        x = numpy.amin(xa)
        y = numpy.amin(ya)
        w = numpy.amax(xa) - x
        h = numpy.amax(ya) - y
        right = 320 + x, y, w, h

        return left, right

    def extract_detection_band(self, left_stick, right_stick):
        x_left, y_left, width_left, heigth_left = left_stick
        x_right, y_right, width_right, heigth_right = right_stick

        y_min = min(y_left, y_right)
        y_max = max(y_left + heigth_left, y_right + heigth_right)

        x_min = x_left + width_left
        x_max = x_right

        return x_min + 1, y_min, x_max - x_min - 2, y_max - y_min

    def extract_borders(self, depth, detection_band):
        result = []

        MAX_DEPTH = 900

        x, y, w, h = detection_band
        for col in range(w):
            for row in reversed(range(h)):
                d = depth[y + row, x + col]
                if d < MAX_DEPTH:  # < self.KINECT_DEPTH_NAN:
                    result.append((x + col, y + row, d))
                    break

        return result

    def analyze_borders(self, borders):

        MAX_BORDER_HEIGHT = 10

        # Separate disconnected zones.
        zones = []
        x, _, _ = borders[0]
        prev = x
        foot = []
        for x, y, d in borders:
            # FIXME Should also check depth biggest variations?
            if x - prev <= 1:
                foot.append((x, y, d))
            else:
                zones.append(foot)
                foot = [(x, y, d)]
            prev = x
        if foot:
            zones.append(foot)

        # Limit zone heigth.
        result = []
        for foot in zones:
            m = max(y for _, y, _ in foot)
            result.append([(x, y, d) for x, y, d in foot
                if m - y <= MAX_BORDER_HEIGHT])

        return result


class KinectDisplay(gtk.DrawingArea):

    def __init__(self, kinect):

        gtk.DrawingArea.__init__(self)
        self.set_size_request(1280, 480)

        self._found = False
        self._rgb_surface = None
        self._depth_surface = None
        self._kinect = kinect

        self._observers = []

        self._x = -1
        self._y = -1
        self._left_stick, self._right_stick = None, None
        self._detection_zone = None
        self._foot = None
        self.refresh_data()

        self.add_events(gtk.gdk.MOTION_NOTIFY
                | gtk.gdk.BUTTON_PRESS
                | gtk.gdk.LEAVE_NOTIFY
                | gtk.gdk.LEAVE_NOTIFY_MASK)
        self.connect("motion_notify_event", self.motion_notify)
        self.connect("leave_notify_event", self.leave_notify)

        self.connect("expose_event", self.expose)

    def add_observer(self, observer):
        self._observers.append(observer)

    def _notify_observers(self):
        data = {}
        data['cursor'] = self._x, self._y

        for observer in self._observers:
            observer.observable_changed(data)

    def leave_notify(self, widget, event):
        self._x, self._y = -1, -1
        self._notify_observers()
        self.queue_draw()

    def motion_notify(self, widget, event):
        x, y = event.x, event.y

        if x >= 640:
            x -= 640

        self._x, self._y = x, y
        self._notify_observers()
        self.queue_draw()

    def expose(self, widget, event):
        self.context = widget.window.cairo_create()
        self.draw(self.context)
        return False

    def refresh_data(self):
        # Get data.
        self._found_kinect, rgb, depth = self._kinect.get_frames()

        # Perform basic extractions.
        o = DepthAnalyser(depth)
        l, r = o.find_sticks()
        self._left_stick, self._right_stick = l, r
        dz = o.extract_detection_band(l, r)
        self._detection_zone = dz
        lb = o.extract_borders(depth, dz)
        f = o.analyze_borders(lb)
        self._foots = f

        # Convert numpy arrays to cairo surfaces.
        alphas = numpy.ones((480, 640, 1), dtype=numpy.uint8) * 255

        # 1. RGB bitmap.
        rgb32 = numpy.concatenate((alphas, rgb), axis=2)
        self._rgb_surface = cairo.ImageSurface.create_for_data(
                rgb32[:, :, ::-1].astype(numpy.uint8),
                cairo.FORMAT_ARGB32, 640, 480)

        # 2. Depth map, take care of special NaN value.
        i = numpy.amin(depth)
        depth_clean = numpy.where(depth == 2047, 0, depth)
        a = numpy.amax(depth_clean)
        depth = numpy.where(
                depth == 2047, 0, 255 - (depth - i) * 254.0 / (a - i))
        depth32 = numpy.dstack(
                (alphas, depth, numpy.where(depth == 0, 128, depth), depth))
        self._depth_surface = cairo.ImageSurface.create_for_data(
                depth32[:, :, ::-1].astype(numpy.uint8),
                cairo.FORMAT_ARGB32, 640, 480)

        self._notify_observers()

    def draw(self, ctx):

        # Draw surfaces.
        ctx.save()
        ctx.move_to(0, 0)
        ctx.set_source_surface(self._rgb_surface)
        ctx.paint()

        ctx.translate(640, 0)
        ctx.set_source_surface(self._depth_surface)
        ctx.paint()

        ctx.restore()

        # Trace lines.
        if self._x >= 0 and self._y >= 0:
            ctx.set_source_rgb(1.0, 0.0, 0.0)
            ctx.set_line_width(1)

            ctx.move_to(0, self._y)
            ctx.line_to(1280, self._y)
            ctx.stroke()

            ctx.move_to(self._x, 0)
            ctx.line_to(self._x, 480)
            ctx.stroke()

            ctx.move_to(self._x + 640, 0)
            ctx.line_to(self._x + 640, 480)
            ctx.stroke()

            # Tell about center_depth.
            depth = self._kinect.latest_depth[self._y, self._x]
            distance = self._kinect.depth_to_cm(depth)
            if distance > 0:
                text = "(%d, %d) - distance: %0.0f cm (depth = %d)" \
                        % (self._x, self._y, distance, depth)
            else:
                text = "(%d, %d)" % (self._x, self._y)

            ctx.select_font_face('Sans')
            ctx.set_font_size(16)
            ctx.move_to(950, 475)
            ctx.set_source_rgb(1, 1, 1)
            ctx.show_text(text)
            ctx.stroke()

        # Draw sticks rectangles and detection zone.
        ctx.set_line_width(1)
        ctx.set_source_rgb(1, 1, 0)

        x, y, w, h = self._left_stick
        ctx.rectangle(x + 640, y, w, h)
        ctx.stroke()

        x, y, w, h = self._right_stick
        ctx.rectangle(x + 640, y, w, h)
        ctx.stroke()

        ctx.set_source_rgb(1, 0, 1)
        x, y, w, h = self._detection_zone
        ctx.rectangle(x + 640, y, w, h)
        ctx.stroke()

        # Draw detected feet in detection zone.
        ctx.set_line_width(2)
        ctx.set_source_rgb(1, 0, 0)
        for foot in self._foots:
            x, y, _ = foot[0]
            ctx.move_to(640 + x, y)
            for x, y, _ in foot[1:]:
                ctx.line_to(640 + x, y)
            ctx.stroke()

        # Tell if images are not from a present device.
        if not self._found_kinect:
            ctx.select_font_face('Sans')
            ctx.set_font_size(20)
            ctx.move_to(20, 20)
            ctx.set_source_rgb(0.0, 0.0, 1.0)
            ctx.show_text("No Kinect detected, using static picture from disk")
            ctx.stroke()


class GameSceneArea(gtk.DrawingArea):

    def __init__(self, kinect):
        gtk.DrawingArea.__init__(self)
        self.set_size_request(640, 480)
        self.connect("expose_event", self.expose)

        self._kinect = kinect
        self._z = -1

    def expose(self, widget, event):
        self.context = widget.window.cairo_create()
        self.draw(self.context)
        return False

    def observable_changed(self, data):
        x, y = data['cursor']
        try:
            depth = self._kinect.latest_depth[y, x]
            self._z = int(self._kinect.depth_to_cm(depth))
        except TypeError:
            self._z = -1
        self.queue_draw()

    def draw(self, ctx):

        # Kinect detection cone.
        ctx.set_line_width(.5)
        ctx.set_source_rgb(0.0, 0.0, 0.0)

        ctx.move_to(320, 479)
        ctx.line_to(0, 0)
        ctx.stroke()

        ctx.move_to(320, 479)
        ctx.line_to(640, 0)
        ctx.stroke()

        # Sticks.
        ctx.set_line_width(2)
        ctx.set_source_rgb(0.0, 0.0, 1.0)

        ctx.arc(250, 350, 5, 0, 2 * math.pi)
        ctx.stroke()
        ctx.arc(390, 350, 5, 0, 2 * math.pi)
        ctx.stroke()

        # Gaming zone.
        ctx.rectangle(80, 0, 480, 360)
        ctx.stroke()

        # Distance indication.
        ctx.set_line_width(.5)

        # d1 (Inter-stick distance).
        ctx.set_source_rgb(0.0, 0.5, 0.0)

        ctx.move_to(255, 350)
        ctx.line_to(385, 350)
        ctx.stroke()

        ctx.select_font_face('Sans')
        ctx.set_font_size(16)
        ctx.move_to(310, 345)
        ctx.show_text('d1')
        ctx.stroke()

        ctx.move_to(500, 435)
        ctx.show_text('d1 = 1.0 m')
        ctx.stroke()

        # d2 (Kinect-stick distance).
        ctx.set_source_rgb(0.5, 0.0, 0.0)

        ctx.move_to(270, 350)
        ctx.line_to(270, 480)
        ctx.stroke()

        ctx.set_font_size(16)
        ctx.move_to(250, 440)
        ctx.show_text('d2')
        ctx.stroke()

        ctx.move_to(500, 455)
        ctx.show_text('d2 = 1.0 m')
        ctx.stroke()

        # Current cursor depth.
        if self._z >= 0:

            # Draw line.
            ctx.set_line_width(1)
            ctx.set_source_rgb(1.0, 0.0, 0.0)
            y = 450 - self._z
            ctx.move_to(0, y)
            ctx.line_to(640, y)
            ctx.stroke()

            # Add distance info.
            ctx.set_line_width(0.5)
            ctx.move_to(30, y)
            ctx.line_to(30, 480)
            ctx.stroke()

            ctx.set_font_size(16)
            ctx.move_to(20, 440)
            ctx.show_text('z')
            ctx.stroke()

            ctx.move_to(500, 475)
            ctx.show_text('z = %2.2f m' % (self._z / 100.0))
            ctx.stroke()


class KinectTestWindow(gtk.Window):

    def __init__(self):
        self._paused = False
        self._kinect = Kinect()

        gtk.Window.__init__(self)
        self.set_default_size(1280, 960)

        vbox = gtk.VBox()
        self.add(vbox)

        # Kinect info visualisation.
        self._display = KinectDisplay(self._kinect)
        vbox.pack_start(self._display, True, True, 0)

        hbox = gtk.HBox()
        vbox.pack_start(hbox)

        # Game scheme representation.
        game_scene = GameSceneArea(self._kinect)
        self._display.add_observer(game_scene)
        hbox.pack_start(game_scene)

        button_vbox = gtk.VBox()
        hbox.pack_start(button_vbox)

        # Save button.
        self.save = gtk.Button('Save', gtk.STOCK_SAVE)
        self.save.set_sensitive(False)
        button_vbox.pack_start(self.save)
        self.save.connect("clicked", self._save_cb)

        # Pause/Autorefresh button.
        self.pause = gtk.Button('Pause', gtk.STOCK_MEDIA_PAUSE)
        button_vbox.pack_start(self.pause)
        self.pause.connect("clicked", self._pause_cb)

        # Auto-refresh at 10 frames per seconds.
        self.timer_id = gobject.timeout_add(100, self._timedout)

        self.connect("destroy", gtk.main_quit)
        self.show_all()

    def _save_cb(self, widget, data=None):
        rgb = self._kinect.latest_rgb
        depth = self._kinect.latest_depth
        fname_base = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())
        numpy.save(fname_base + '_rgb', rgb)
        numpy.save(fname_base + '_depth', depth)
        print 'Saved with "%s" base filename' % fname_base

    def _pause_cb(self, widget, data=None):
        self._paused = not self._paused
        self.save.set_sensitive(self._paused)

        if not self._paused:
            self.pause.set_label(gtk.STOCK_MEDIA_PAUSE)
            # Try to prevent unwanted redraw.
            if not data:
                self._display.refresh_data()
                self.queue_draw()
            self.timer_id = gobject.timeout_add(100, self._timedout)
        else:
            self.pause.set_label(gtk.STOCK_REFRESH)

    def _timedout(self):
        # Stop auto refresh if no Kinect is detected.
        if self._kinect.latest_present:
            self._display.refresh_data()
            self.queue_draw()
        else:
            if not self._paused:
                print 'No Kinect found, stopping auto-refresh'
                self._pause_cb(None, True)

        # Timer is repeated until False is returned.
        return not self._paused

    def run(self):
        gtk.main()


def main():
    KinectTestWindow().run()

if __name__ == "__main__":
    main()
