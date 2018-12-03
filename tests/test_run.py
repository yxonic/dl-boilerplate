import py
import pytest
from _pytest.capture import CaptureFixture

import app.command
import app.common
import app.models
from app.models import Model


class ModelTest(Model):
    @classmethod
    def _add_arguments(cls, parser):
        parser.add_argument('-x', default=10, type=int)


def dummy(ws, args):
    return ws, args


# insert model and command for testing
app.models.ModelTest = ModelTest
app.command.train = dummy
app.command.test = dummy


def test_main(tmpdir: py.path.local, capsys: CaptureFixture):
    """Test main workflow."""

    # temporary workspace
    ws = tmpdir.join('ws')
    ws_path = str(ws)

    import app.run

    # error if workspace command called before config
    with pytest.raises(app.common.NotConfiguredError):
        args = app.run.main_parser.parse_args(
            ['-w', ws_path, 'train']
        )
        w, _ = app.run.main(args)
        _ = w.model

    # test config
    args = app.run.main_parser.parse_args(
        ['-w', ws_path, 'config', 'ModelTest']
    )
    app.run.main(args)
    assert ws.join('config.toml').check(file=1)
    assert capsys.readouterr().err.strip().endswith(
        'configured ModelTest with {\'x\': 10}')

    args = app.run.main_parser.parse_args(
        ['-w', ws_path, 'config', 'ModelTest', '-x=-3']
    )
    app.run.main(args)
    assert ws.join('config.toml').check(file=1)
    assert capsys.readouterr().err.strip().endswith(
        'configured ModelTest with {\'x\': -3}')

    # test train/test args
    args = app.run.main_parser.parse_args(
        ['-w', ws_path, 'train', '-N', '3']
    )
    w, args = app.run.main(args)
    assert w.model.config.x == -3
    assert args.epochs == 3

    args = app.run.main_parser.parse_args(
        ['-w', ws_path, 'test', '-s', '15']
    )
    w, args = app.run.main(args)
    assert w.model.config.x == -3
    assert args.snapshot == '15'

    # test clean
    args = app.run.main_parser.parse_args(
        ['-w', ws_path, 'clean']
    )
    app.run.main(args)
    assert ws.join('config.toml').check(file=1)

    args = app.run.main_parser.parse_args(
        ['-w', ws_path, 'clean', '--all']
    )
    app.run.main(args)
    assert not ws.exists()

    # print usage on wrong command-line arguments
    with pytest.raises(SystemExit) as e:
        args = app.run.main_parser.parse_args(
            ['-w', ws_path, 'foo']
        )
        app.run.main(args)
    assert e.value.code == 2
    assert capsys.readouterr().err.strip().startswith('usage:')

    # reset logging state as app.run.main messed up with it
    import logging
    import importlib
    logging.shutdown()
    importlib.reload(logging)
