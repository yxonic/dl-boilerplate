import app.util


def test_colored():
    # test colored output w/o bold font
    assert app.util.colored('hello', 'red') == \
        '\x1b[91mhello\x1b[0m'
    assert app.util.colored('hello', 'red', True) == \
        '\x1b[1m\x1b[91mhello\x1b[0m'
