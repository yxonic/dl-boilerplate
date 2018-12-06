"""
Main program parsing arguments and running commands.
"""
from __future__ import print_function

import argparse
import inspect as ins
import logging
import sys

from . import command
from . import common
from . import util


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # customize error message
        self.print_usage(sys.stderr)
        err = util.colored('error:', 'red', True)
        self.exit(2, '%s %s\n' % (err, message))


_parser_formatter = argparse.ArgumentDefaultsHelpFormatter
main_parser = _ArgumentParser(formatter_class=_parser_formatter,
                              prog='python -m app.run')
main_parser.add_argument('-w', '--workspace',
                         help='workspace dir', default='ws/test')
main_parser.add_argument('-q', action='store_true', help='quiet')
main_parser.add_argument('-v', action='store_true', help='verbose')
_subparsers = main_parser.add_subparsers(title='supported commands',
                                         dest='command')
_subparsers.required = True
_subparser_map = {}

_commands = {m[0].lower(): m[1]
             for m in ins.getmembers(command,
                                     util.sub_class_checker(common.Command))}

for _cmd in _commands:
    _sub = _subparsers.add_parser(_cmd,
                                  formatter_class=_parser_formatter)
    _subparser_map[_cmd] = _sub
    _sub.set_defaults(func=_commands[_cmd](_sub)._run)


def main(args):
    logger = logging.getLogger(args.command)
    try:
        return args.func(args)
    except KeyboardInterrupt:  # pragma: no cover
        # print traceback info to screen only
        import traceback
        sys.stderr.write(traceback.format_exc())
        logger.warning('cancelled by user')
    except common.NotConfiguredError as e:  # pragma: no cover
        print('error:', e)
        _subparser_map['config'].print_usage()
        sys.exit(1)
    except Exception as e:  # pragma: no cover
        # print traceback info to screen only
        import traceback
        sys.stderr.write(traceback.format_exc())
        logger.error('exception occurred: %s', e)


if __name__ == '__main__':
    _args = main_parser.parse_args()

    # configure logger
    _logger = logging.getLogger()
    if _args.q:
        _logger.setLevel(logging.WARNING)
    elif _args.v:
        _logger.setLevel(logging.DEBUG)
    else:
        _logger.setLevel(logging.INFO)

    class _ColoredFormatter(logging.Formatter):
        _LOG_COLORS = {
            'WARNING': 'yellow',
            'INFO': 'green',
            'DEBUG': 'blue',
            'CRITICAL': 'yellow',
            'ERROR': 'red'
        }

        def format(self, record):
            levelname = record.levelname
            if levelname in self._LOG_COLORS:
                record.levelname = util.colored(
                    record.levelname[0], self._LOG_COLORS[record.levelname])
            return logging.Formatter.format(self, record)

    logFormatter = _ColoredFormatter(
        '%(levelname)s [%(name)s] %(asctime)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    _logger.addHandler(consoleHandler)

    # remove logging related options
    del _args.q
    del _args.v

    main(_args)
