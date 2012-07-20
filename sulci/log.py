import logging
import logging.handlers

from sulci import config


class MemoryStorageHandler(logging.handlers.MemoryHandler):
    """
    All the logging info is stored in a python list.
    """
    def flush(self):
        for record in self.buffer:
            self.target.append(record)
        self.buffer = []


class ConsoleColorFormatter(logging.Formatter):
    """
    Add color for a console output.
    """
    def format(self, record):
        colors = {
              "GRAY": 0,
              "RED": 1,
              "GREEN": 2,
              "YELLOW": 3,
              "BLUE": 4,
              "MAGENTA": 5,
              "CYAN": 6,
              "WHITE": 7,
              "CRIMSON": 8
             }
        prefix = suffix = u""
        if hasattr(record, "color") and record.color in colors:
            base = hasattr(record, "highlight") and record.highlight and 40 or 30
            prefix = u"\033[1;%sm" % (base + colors[record.color])
            suffix = u"\033[1;m"
            record.msg = u"%s%s%s" % (prefix, record.msg, suffix)
        return logging.Formatter.format(self, record)


class HTMLColorFormatter(logging.Formatter):
    """
    Add CSS style and HTML tag for HTML output.
    """
    def format(self, record):
        style = u""
        if hasattr(record, "color") :
            color_type = record.highlight and "background-color" or "color"
            weight = record.highlight and "bold" or "normal"
            style = "%s:%s; font-weight:%s;" % (color_type, record.color, weight)
        prefix = u'<span style="%s">' % style
        suffix = u"</span>"
        record.msg = u"%s%s%s" % (prefix, record.msg, suffix)
        return logging.Formatter.format(self, record)


# Custom logger class
class ColoredLogger(logging.Logger):
    """
    This logger allow to define a color.
    This color will be added as property to the LogRecord object.
    An optional highlight parameter define if the color will be of the font
    or the background.
    """
    def log(self, lvl, msg, color="GREEN", highlight=False):
        """
        Add color parameter and pass it to log via extra parameter.
        This parameter will be added as property to the LogRecord.
        """
        logging.Logger.log(self, lvl, msg, extra={"color": color, "highlight": highlight})

    def debug(self, msg, color="GREEN", highlight=False):
        self.log(logging.DEBUG, msg, color, highlight)

    def info(self, msg, color="WHITE", highlight=False):
        self.log(logging.INFO, msg, color, highlight)

logging.setLoggerClass(ColoredLogger)

# Remove default handlers (is it a better way to do this ?)
root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)

# Make a global logging object.
sulci_logger = ColoredLogger("sulci")
# We always set level to DEBUG
sulci_logger.setLevel(logging.DEBUG)
# We add a console handler
h = logging.StreamHandler()
# We set a debug level to console only if debug is True
if config.DEBUG:
    h.setLevel(logging.DEBUG)
else:
    h.setLevel(logging.INFO)
f = ConsoleColorFormatter("[%(levelname)s] %(message)s")
h.setFormatter(f)
sulci_logger.addHandler(h)


#h = logging.StreamHandler()
#f = logging.Formatter("[%(levelname)s] %(message)s")
#h.setFormatter(f)
#sulci_logger.addHandler(h)
