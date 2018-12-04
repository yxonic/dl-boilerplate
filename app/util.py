import re


def wrap_parser(namespace, parser):  # pragma: no cover
    """Wraps an argument parser, putting all following options under a namespace."""
    robj = re.compile(r'^(-+)')

    class _Wrapper:
        def __init__(self, _parser):
            self.parser = _parser

        def add_argument(self, *args, **kwargs):
            args = [robj.sub(r'\1' + namespace + '.', s) for s in args]
            self.parser.add_argument(*args, **kwargs)

    return _Wrapper(parser)


def colored(text, color, bold=False):
    """Generate colored output.

    Args:
        text (str): text to be colored
        color (str): color name
        bold (bool): output bold text (default: ``False``)
    """
    color = getattr(_BColors, color)
    if bold:
        return _BColors.bold + color + text + _BColors.end
    else:
        return color + text + _BColors.end


class _BColors:
    header = '\033[95m'
    blue = '\033[94m'
    green = '\033[92m'
    yellow = '\033[93m'
    red = '\033[91m'
    end = '\033[0m'
    bold = '\033[1m'
    underline = '\033[4m'
