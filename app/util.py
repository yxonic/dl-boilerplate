import argparse
import logging
import os
import re
import sys

import toml


def _unfold_config(cfg):  # pragma: no cover
    for k, v in cfg.items():
        if isinstance(v, dict):
            _unfold_config(v)
        if '.' not in k:
            continue
        d = cfg
        for sec in k.split('.')[:-1]:
            if sec in d:
                d = d[sec]
            else:
                d[sec] = {}
                d = d[sec]
        d[k.split('.')[-1]] = v
        del cfg[k]


def save_config(workspace, config):
    """Save configuration to ``workspace``."""
    cfg = load_config(workspace)
    cfg.update(config)
    _unfold_config(cfg)
    f = open(os.path.join(workspace, 'config.toml'), 'w')
    toml.dump(cfg, f)
    f.close()


def load_config(workspace):
    """Load configuration from ``workspace``."""
    try:
        config = toml.load(open(os.path.join(workspace, 'config.toml'), 'r'))
        return config
    except OSError:
        return {}


def namespace_subparser(namespace, parser):  # pragma: no cover
    robj = re.compile(r'^(-+)')

    class _Wrapper:
        def __init__(self, _parser):
            self.parser = _parser

        def add_argument(self, *args, **kwargs):
            args = [robj.sub(r'\1' + namespace + '.', s) for s in args]
            self.parser.add_argument(*args, **kwargs)

    return _Wrapper(parser)


class _BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def _colored(text, color, bold=False):
    if bold:
        return _BColors.BOLD + color + text + _BColors.ENDC
    else:
        return color + text + _BColors.ENDC


#: Log level to color mapping.
LOG_COLORS = {
    'WARNING': _BColors.WARNING,
    'INFO': _BColors.OKGREEN,
    'DEBUG': _BColors.OKBLUE,
    'CRITICAL': _BColors.WARNING,
    'ERROR': _BColors.FAIL
}


class ColoredFormatter(logging.Formatter):
    """Log formatter that provides colored output."""

    def __init__(self, fmt, datefmt):
        """
        Args:
            fmt (str): message format string
            datefmt (str): date format string
        """
        super().__init__(fmt, datefmt)

    def format(self, record):
        """Format the specified record as text.

        If ``self.use_color`` is ``True``, format log messages according to
        :data:`~app.utils.LOG_COLORS`.
        """
        levelname = record.levelname
        if levelname in LOG_COLORS:
            record.levelname = _colored(record.levelname[0],
                                        LOG_COLORS[record.levelname])
        return logging.Formatter.format(self, record)


class _ArgumentParser(argparse.ArgumentParser):
    def __init__(self, raise_error=False, **kwargs):
        super().__init__(**kwargs)
        self.raise_error = raise_error

    def error(self, message):
        if self.raise_error:
            raise ValueError(message)
        # customize error message
        self.print_usage(sys.stderr)
        err = _colored('error:', LOG_COLORS['ERROR'], True)
        self.exit(2, '%s %s\n' % (err, message))
