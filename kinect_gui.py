from freenect import sync_get_depth as get_depth, sync_get_video as get_video

import pygtk
pygtk.require('2.0')
import gtk

import cairo

import numpy

class KinectDisplay(gtk.DrawingArea):

    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event", self.expose)

    def expose(self, widget, event):
        self.context = widget.window.cairo_create()
        self.draw(self.context)
        return False

    def draw(self, ctx):

        found_kinect = False
        try:
            # Try to obtain Kinect images.
            (depth, _), (rgb, _) = get_depth(), get_video()
            found_kinect = True
        except TypeError:
            rgb = numpy.load('2012-03-02_14-36-48_rgb.npy')
            depth = numpy.load('2012-03-02_14-36-48_depth.npy')

        # Convert numpy arrays to cairo surfaces.
        alphas = numpy.ones((480, 640, 1), dtype=numpy.uint8) * 255
        rgb32 = numpy.concatenate((alphas, rgb), axis=2)
        rgb_surface = cairo.ImageSurface.create_for_data(
                rgb32[:,:,::-1].astype(numpy.uint8),
                cairo.FORMAT_ARGB32, 640, 480)

        # Idem with depth, but take care of special NaN value.
        i = numpy.amin(depth)
        depth_clean = numpy.where(depth == 2047, 0, depth)
        a = numpy.amax(depth_clean)
        print i, a
        depth = numpy.where(depth == 2047, 0, 255 - (depth - i) * 254.0 / (a - i))
        depth32 = numpy.dstack((alphas, depth, numpy.where(depth == 0, 128, depth), depth))
        depth_surface = cairo.ImageSurface.create_for_data(
                depth32[:,:,::-1].astype(numpy.uint8),
                cairo.FORMAT_ARGB32, 640, 480)


        # Draw surfaces.
        ctx.save()
        ctx.move_to(0, 0)
        ctx.set_source_surface(rgb_surface)
        ctx.paint()

        ctx.translate(640, 0)
        ctx.set_source_surface(depth_surface)
        ctx.paint()

        ctx.restore()

        if not found_kinect:
            ctx.select_font_face('Sans')
            ctx.set_font_size(20)
            ctx.move_to(20, 20)
            ctx.set_source_rgb(0.0, 0.0, 1.0)
            ctx.show_text("No Kinect detected, using static picture from disk")
            ctx.stroke()


def main():

    window = gtk.Window()
    window.set_default_size(1280, 480)
    display = KinectDisplay()

    window.add(display)
    window.connect("destroy", gtk.main_quit)
    window.show_all()

    gtk.main()

if __name__ == "__main__":
    main()
