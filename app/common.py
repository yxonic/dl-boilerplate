import abc
import argparse
import functools
import logging
import pathlib
from collections import namedtuple

import toml

from . import util


class NotConfiguredError(Exception):
    pass


class Model(abc.ABC):
    """Interface for model that can save/load parameters.

    Each model class should have an ``_add_argument`` class method to define
    model arguments along with their types, default values, etc.
    """

    @classmethod
    @abc.abstractmethod
    def _add_arguments(cls, parser: argparse.ArgumentParser):
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
        config = namedtuple(cls.__name__ + 'Conf', kwargs.keys())(*kwargs.values())
        return cls(config)

    @classmethod
    def parse(cls, args):
        """Parse command-line options and build model."""
        parser = util._ArgumentParser(prog='', add_help=False,
                                      raise_error=True)
        cls._add_arguments(parser)
        args = parser.parse_args(args)
        return cls.build(**dict(args._get_kwargs()))

    def __init__(self, config):
        """
        Args:
            config (namedtuple): model configuration
        """
        self.config = config


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
    def config(self):
        if self._config is not None:
            return self._config
        try:
            cfg = toml.load((self.path / 'config.toml').open())
        except FileNotFoundError:
            cfg = {}
        self._config = cfg
        return cfg

    @property
    @functools.lru_cache()
    def model(self):
        if 'model' not in self.config:
            raise NotConfiguredError('config.toml doesn\'t exist or is incomplete')
        from . import models
        model_cls = getattr(models, self.config['model'])
        return model_cls.build(**self.config['config'])

    @functools.lru_cache()
    def logger(self, name: str):
        """Get a logger that logs to a file. Notice that same logger instance is returned for same names."""
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

    def update_config(self, config):
        """Update configuration."""
        cfg = self.config
        cfg.update(config)
        util._unfold_config(cfg)
        self._config = cfg

    def save_config(self):
        """Save configuration."""
        f = (self.path / 'config.toml').open('w')
        toml.dump(self.config, f)
        f.close()
