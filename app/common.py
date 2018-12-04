import abc
import argparse
import logging
import pathlib
from collections import namedtuple

import toml


class NotConfiguredError(Exception):
    pass


class ParseError(Exception):
    pass


class Model(abc.ABC):
    """Interface for model that can save/load parameters.

    Each model class should have an ``_add_argument`` class method to define
    model arguments along with their types, default values, etc.
    """

    @classmethod
    @abc.abstractmethod
    def add_arguments(cls, parser: argparse.ArgumentParser):
        """Add arguments to an argparse subparser."""
        raise NotImplementedError

    @classmethod
    def build(cls, **kwargs):
        """Build model. Parameters are specified by keyword arguments.

        Example:
            >>> from models import Simple
            >>> model = Simple.build(foo=3)
            >>> print(model.config)
            Config(foo=3)
        """
        config = namedtuple(cls.__name__, kwargs.keys())(*kwargs.values())
        return cls(config)

    @classmethod
    def parse(cls, args):
        """Parse command-line options and build model."""

        class _ArgumentParser(argparse.ArgumentParser):
            def error(self, message):
                raise ParseError(message)

        parser = _ArgumentParser(prog='', add_help=False)
        cls.add_arguments(parser)
        args = parser.parse_args(args)
        config = dict(args._get_kwargs())
        Model._unfold_config(config)
        return cls.build(**config)

    def __init__(self, config):
        """
        Args:
            config (namedtuple): model configuration
        """
        self.config = config

    def __str__(self):
        return str(self.config)

    @staticmethod
    def _unfold_config(cfg):
        for k, v in list(cfg.items()):
            if isinstance(v, dict):
                Model._unfold_config(v)
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


class Workspace:
    """Workspace utilities. One can save/load configurations, build models
    with specific configuration, save snapshots, open results, etc., using
    workspace objects."""

    def __init__(self, path: str):
        self._path = pathlib.Path(path)
        self._log_path = self._path / 'log'
        self._snapshot_path = self._path / 'snapshot'
        self._result_path = self._path / 'result'
        self._config = None
        self._model_name = None

    def __str__(self):
        return str(self.path)

    def __repr__(self):
        return 'Workspace(path=' + str(self.path) + ')'

    @property
    def path(self):
        if not self._path.exists():
            self._path.mkdir(parents=True)
        return self._path

    @property
    def result_path(self):
        if not self._result_path.exists():
            self._result_path.mkdir(parents=True)
        return self._result_path

    @property
    def snapshot_path(self):
        if not self._snapshot_path.exists():
            self._snapshot_path.mkdir(parents=True)
        return self._snapshot_path

    @property
    def log_path(self):
        if not self._log_path.exists():
            self._log_path.mkdir(parents=True)
        return self._log_path

    @property
    def model_name(self):
        if self._model_name is not None:
            return self._model_name
        _ = self.config
        return self._model_name

    @property
    def config(self):
        if self._config is not None:
            return self._config
        try:
            cfg = toml.load((self.path / 'config.toml').open())
            self._model_name = cfg['model_name']
            self._config = cfg[self.model_name.lower()]
        except (FileNotFoundError, KeyError):
            raise NotConfiguredError('config.toml doesn\'t exist or is incomplete')
        return self._config

    def set_model(self, name, config):
        self._model_name = name
        self._config = config
        self._save_config()

    def build_model(self):
        """Build model according to the configurations in current workspace."""
        from . import models
        model_cls = getattr(models, self.model_name)
        return model_cls.build(**self.config)

    def logger(self, name: str):
        """Get a logger that logs to a file.

        Notice that same logger instance is returned for same names.

        Args:
            name(str): logger name
        """
        logger = logging.getLogger(name)
        if logger.handlers:
            # previously configured, remain unchanged
            return logger
        fileFormatter = logging.Formatter('%(levelname)s [%(name)s] %(asctime)s %(message)s',
                                          datefmt='%Y-%m-%d %H:%M:%S')
        fileHandler = logging.FileHandler(str(self.log_path / (name + '.log')))
        fileHandler.setFormatter(fileFormatter)
        logger.addHandler(fileHandler)
        return logger

    def _save_config(self):
        """Save configuration."""
        f = (self.path / 'config.toml').open('w')
        toml.dump({'model_name': self.model_name, self.model_name.lower(): self.config}, f)
        f.close()


class Command(abc.ABC):
    """Command interface."""

    def __init__(self, parser):
        self.parser = parser

    def _run(self, args):
        ws = Workspace(args.workspace)
        cmd = args.command
        del args.command, args.func, args.workspace
        args = {name: value for (name, value) in args._get_kwargs()}
        args = namedtuple(cmd.capitalize(), args.keys())(*args.values())
        return self.run(ws, args)

    @abc.abstractmethod
    def run(self, ws, args):
        raise NotImplementedError
