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


class Kinect(object):

    def __init__(self):
        self.latest_rgb = None
        self.latest_depth = None
        self.latest_present = False

    def get_frames(self):

        found_kinect = False
        try:
            # Try to obtain Kinect images.
            (depth, _), (rgb, _) = get_depth(), get_video()
            found_kinect = True
        except TypeError:
            rgb = numpy.load('2012-03-02_14-36-48_rgb.npy')
            depth = numpy.load('2012-03-02_14-36-48_depth.npy')

        self.latest_rgb = rgb
        self.latest_depth = depth
        self.latest_present = found_kinect

        return found_kinect, rgb, depth


class KinectDisplay(gtk.DrawingArea):

    def __init__(self, kinect):

        self._kinect = kinect

        gtk.DrawingArea.__init__(self)
        self.set_size_request(1280, 480)
        self.connect("expose_event", self.expose)

    def expose(self, widget, event):
        self.context = widget.window.cairo_create()
        self.draw(self.context)
        return False

    def draw(self, ctx):

        found_kinect, rgb, depth = self._kinect.get_frames()

        # Convert numpy arrays to cairo surfaces.
        alphas = numpy.ones((480, 640, 1), dtype=numpy.uint8) * 255
        rgb32 = numpy.concatenate((alphas, rgb), axis=2)
        rgb_surface = cairo.ImageSurface.create_for_data(
                rgb32[:, :, ::-1].astype(numpy.uint8),
                cairo.FORMAT_ARGB32, 640, 480)

        # Idem with depth, but take care of special NaN value.
        i = numpy.amin(depth)
        center_depth = depth[240, 320]
        depth_clean = numpy.where(depth == 2047, 0, depth)
        a = numpy.amax(depth_clean)
        depth = numpy.where(
                depth == 2047, 0, 255 - (depth - i) * 254.0 / (a - i))
        depth32 = numpy.dstack(
                (alphas, depth, numpy.where(depth == 0, 128, depth), depth))
        depth_surface = cairo.ImageSurface.create_for_data(
                depth32[:, :, ::-1].astype(numpy.uint8),
                cairo.FORMAT_ARGB32, 640, 480)

        # Draw arrays.
        ctx.save()
        ctx.move_to(0, 0)
        ctx.set_source_surface(rgb_surface)
        ctx.paint()

        ctx.translate(640, 0)
        ctx.set_source_surface(depth_surface)
        ctx.paint()

        ctx.restore()

        # Trace lines.
        ctx.set_source_rgb(1.0, 0.0, 0.0)
        ctx.set_line_width(.5)

        ctx.move_to(0, 240)
        ctx.line_to(1280, 240)
        ctx.stroke()

        ctx.move_to(320, 0)
        ctx.line_to(320, 480)
        ctx.stroke()

        ctx.move_to(960, 0)
        ctx.line_to(960, 480)
        ctx.stroke()

        # Tell about center_depth.
        print center_depth
        ctx.select_font_face('Sans')
        ctx.set_font_size(16)
        ctx.move_to(1100, 475)
        ctx.set_source_rgb(0.2, 0.2, 0.8)
        ctx.show_text("Central pixel depth: %d" % center_depth)
        ctx.stroke()

        # Tell if images are not from a present device.
        if not found_kinect:
            ctx.select_font_face('Sans')
            ctx.set_font_size(20)
            ctx.move_to(20, 20)
            ctx.set_source_rgb(0.0, 0.0, 1.0)
            ctx.show_text("No Kinect detected, using static picture from disk")
            ctx.stroke()


class KinectTestWindow(gtk.Window):

    def __init__(self):
        self._paused = False
        self._kinect = Kinect()

        gtk.Window.__init__(self)
        self.set_default_size(1280, 480 + 32)

        vbox = gtk.VBox()
        self.add(vbox)

        display = KinectDisplay(self._kinect)
        vbox.pack_start(display, True, True, 0)

        hbox = gtk.HBox()
        vbox.pack_start(hbox)

        # Save button.
        self.save = gtk.Button('Save', gtk.STOCK_SAVE)
        self.save.set_sensitive(False)
        hbox.pack_start(self.save)
        self.save.connect("clicked", self._save_cb)

        # Pause/Autorefresh button.
        self.pause = gtk.Button('Pause', gtk.STOCK_MEDIA_PAUSE)
        hbox.pack_start(self.pause)
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
                self.queue_draw()
            self.timer_id = gobject.timeout_add(100, self._timedout)
        else:
            self.pause.set_label(gtk.STOCK_REFRESH)

    def _timedout(self):
        # Stop auto refresh if no Kinect is detected.
        if self._kinect.latest_present:
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
