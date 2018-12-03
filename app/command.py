"""Define commands."""


def train(ws, args):  # pragma: no cover
    """Train the model. See :class:`~app.run.Train` for ``args``."""
    logger = ws.logger('train')
    logger.info('[%s] model: %s, args: %s', ws, ws.model.config, args)


def test(ws, args):  # pragma: no cover
    """Test the model. See :class:`~app.run.Test` for ``args``."""
    logger = ws.logger('test')
    logger.info('[%s] model: %s, args: %s', ws, ws.model.config, args)
