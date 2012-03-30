from freenect import sync_get_depth as get_depth, sync_get_video as get_video
import numpy


class Kinect(object):

    UNDEF_DEPTH = 2047
    UNDEF_DISTANCE = 2000.0

    # Formula from http://vvvv.org/forum/the-kinect-thread.
    _dist_values = numpy.tan(numpy.arange(2048) / 1024.0 + 0.5) * 33.825 + 5.7

    # XBox 360 Kinect is said to be OK with
    # depth values between 80 cm and 4 meters.
    MIN_DISTANCE = 80.0  # cm
    DIST_ARRAY = numpy.where(
            MIN_DISTANCE < _dist_values,
            _dist_values,
            UNDEF_DISTANCE)
    MAX_DISTANCE = 400.0  # cm
    DIST_ARRAY = numpy.where(
            DIST_ARRAY < MAX_DISTANCE,
            DIST_ARRAY,
            UNDEF_DISTANCE)

    _filename = '2012-03-02_14-36-48'

    def __init__(self):
        self._loaded_rgb = None
        self._loaded_depth = None

        self.latest_rgb = None
        self.latest_depth = None
        self.latest_present = False

    def depth_to_cm(self, depth):
        return self.DIST_ARRAY[depth]

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
                        numpy.load(self._filename + '_rgb.npy')
            rgb = self._loaded_rgb

            if self._loaded_depth == None:
                self._loaded_depth = \
                        numpy.load(self._filename + '_depth.npy')
            depth = self._loaded_depth

        # Memorize results.
        self.latest_rgb = rgb
        self.latest_depth = depth
        self.latest_present = found_kinect

        return found_kinect, rgb, depth

    def set_filename(self, filename):
        self._filename = filename
        self._loaded_rgb = None
        self._loaded_depth = None


class DepthAnalyser(object):

    def __init__(self, depth):
        self._depth = depth

        # TODO Limit conversion to detection zone.

        # Convert depth to cm.
        self._distance = Kinect.DIST_ARRAY[depth]
        # TODO Also convert x and y axis to cm here.

    def find_sticks(self):

        # Remove further objects.
        closest = numpy.amin(self._distance)
        STICK_THRESHOLD = 10.0  # cm
        depth_near = numpy.where(
                self._distance < closest + STICK_THRESHOLD, 1, 0)

        # Look for first stick (on the left).
        ya, xa = numpy.nonzero(depth_near[:, :320])
        x_min = numpy.amin(xa)
        y_min = numpy.amin(ya)
        x_max = numpy.amax(xa)
        y_max = numpy.amax(ya)
        dist = numpy.amin(self._distance[y_min:y_max, x_min:x_max])
        left = x_min, y_min, x_max - x_min, y_max - y_min, dist

        # Look for second stick (on the right).
        ya, xa = numpy.nonzero(depth_near[:, 320:])
        x_min = numpy.amin(xa) + 320
        y_min = numpy.amin(ya)
        x_max = numpy.amax(xa) + 320
        y_max = numpy.amax(ya)
        dist = numpy.amin(self._distance[y_min:y_max, x_min:x_max])
        right = x_min, y_min, x_max - x_min, y_max - y_min, dist

        return left, right

    def extract_detection_band(self, left_stick, right_stick):
        x_left, y_left, width_left, heigth_left, _ = left_stick
        x_right, y_right, width_right, heigth_right, _ = right_stick

        y_min = min(y_left, y_right)
        y_max = max(y_left + heigth_left, y_right + heigth_right)

        x_min = x_left + width_left
        x_max = x_right

        return x_min + 1, y_min, x_max - x_min - 2, y_max - y_min

    def extract_borders(self, detection_band):
        result = []

        MAX_DEPTH = 300.0  # 3 meters.

        x, y, w, h = detection_band
        for col in range(w):
            for row in reversed(range(h)):
                z = self._distance[y + row, x + col]
                if z < MAX_DEPTH:
                    result.append((x + col, y + row, z))
                    break

        return result

    def analyze_borders(self, borders):

        MAX_BORDER_HEIGHT = 10  # pixels.

        # Find obstacles in the field.
        zones = []
        x, _, z = borders[0]
        prev_x = x
        prev_z = z
        foot = []
        for x, y, z in borders:
            # Separate disconnected zones.
            if x - prev_x <= 1 and abs(prev_z - z) < 10:
                foot.append((x, y, z))
            else:
                zones.append(foot)
                foot = [(x, y, z)]
            prev_x = x
            prev_z = z
        if foot:
            zones.append(foot)

        # Limit zone heigth.
        result = []
        for foot in zones:
            m = max(y for _, y, _ in foot)
            result.append([(x, y, z) for x, y, z in foot
                if m - y <= MAX_BORDER_HEIGHT])

        return result
