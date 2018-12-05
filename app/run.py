"""
Main program parsing arguments and running commands.
"""
from __future__ import print_function

import argparse
import inspect as ins
import logging
import shutil
import sys
from collections import defaultdict

from . import command
from . import common
from . import models as mm
from . import util


class Train(common.Command):
    """Command ``train``. See :func:`~app.command.train`."""

    def __init__(self, parser):
        """
        Args:
            -N,--epochs (int): number of epochs to train. Default: 10
        """
        super().__init__(parser)
        parser.add_argument('-N', '--epochs', type=int, default=10,
                            help='number of epochs to train')

    def run(self, ws, args):
        return command.train(ws, args)


class Test(common.Command):
    """Command ``test``. See :func:`~app.command.test`."""

    def __init__(self, parser):
        """
        Args:
            -s,--snapshot (str): model snapshot to test with
        """
        super().__init__(parser)
        parser.add_argument('-s', '--snapshot',
                            help='model snapshot to test with')

    def run(self, ws, args):
        return command.test(ws, args)


class Config(common.Command):
    """Command ``config``,

    Configure a model and its parameters for a workspace.

    Example:
        .. code-block:: bash

            $ python app.run -w ws/test config Simple -foo=5
            In [ws/test]: configured Simple with Config(foo='5')
    """

    def __init__(self, parser):
        super().__init__(parser)
        subs = parser.add_subparsers(title='models available', dest='model')
        subs.required = True
        group_options = defaultdict(set)
        _models = [m[0] for m in ins.getmembers(mm,
                                                _sub_class_checker(mm.Model))
                   if not m[0].startswith('_')]
        for model in _models:
            sub = subs.add_parser(model, formatter_class=_parser_formatter)
            group = sub.add_argument_group('config')
            Model = getattr(mm, model)
            Model.add_arguments(group)
            for action in group._group_actions:
                group_options[model].add(action.dest)

            def save(args):
                _model = args.model
                config = {name: value for (name, value) in args._get_kwargs()
                          if name in group_options[_model]}
                Model._unfold_config(config)
                print('In [%s]: configured %s with %s' %
                      (args.workspace, _model, str(config)),
                      file=sys.stderr)

                ws = common.Workspace(args.workspace, _model, config)

            sub.set_defaults(func=save)

    def run(self, ws, args):
        pass


class Clean(common.Command):
    """Command ``clean``.

    Remove all snapshots in specific workspace. If ``--all`` is specified,
    clean the entire workspace
    """

    def __init__(self, parser):
        super().__init__(parser)
        parser.add_argument('--all', action='store_true',
                            help='clean the entire workspace')

    def run(self, ws, args):
        if args.all:
            shutil.rmtree(str(ws))
        else:
            shutil.rmtree(str(ws.snapshot_path))


def _sub_class_checker(cls):
    def rv(obj):
        if ins.isclass(obj) and not ins.isabstract(obj) \
                and issubclass(obj, cls):
            return True
        else:
            return False

    return rv


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
             for m in ins.getmembers(sys.modules[__name__],
                                     _sub_class_checker(common.Command))}
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
