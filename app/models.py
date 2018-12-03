"""
Model classes that defines model parameters and architecture.
"""
import abc
import argparse
from collections import namedtuple

from . import util


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


class Simple(Model):
    """A toy class to demonstrate how to add model arguments."""

    @classmethod
    def _add_arguments(cls, parser):
        parser.add_argument('-foo', default=10, type=int,
                            help='dumb param')


'''
class Complex(Model):
    """A toy class to demonstrate how to put models together."""

    @classmethod
    def _add_arguments(cls, parser):
        Simple._add_arguments(util.namespace_subparser('l1', parser))
        Simple._add_arguments(util.namespace_subparser('l2', parser))

    def __init__(self, config):
        super().__init__(config)
        self.l1 = Simple.build(**config.l1)
        self.l2 = Simple.build(**config.l2)
'''
