import app.models as models


def test_models():
    trainer = models.Trainer.parse(['-l1.foo', '3', '-l2.foo', '4',
                                    '-lr', '0.1'])
    assert trainer.config.lr == 0.1
    assert trainer.l1.config.foo == 3
    assert trainer.l2.config.foo == 4
