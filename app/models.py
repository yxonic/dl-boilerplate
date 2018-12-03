"""
Model classes that defines model parameters and architecture.
"""

from .common import Model
from .util import wrap_parser


class Simple(Model):
    """A toy class to demonstrate how to add model arguments."""

    @classmethod
    def _add_arguments(cls, parser):
        parser.add_argument('-foo', default=10, type=int,
                            help='dumb param')


class Complex(Model):
    """A toy class to demonstrate how to put models together."""

    @classmethod
    def _add_arguments(cls, parser):
        Simple._add_arguments(wrap_parser('l1', parser))
        Simple._add_arguments(wrap_parser('l2', parser))

    def __init__(self, config):
        super().__init__(config)
        self.l1 = Simple.build(**config.l1)
        self.l2 = Simple.build(**config.l2)
