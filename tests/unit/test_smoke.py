"""Smoke test: the package imports and exposes a version."""

import receipt_board


def test_version_is_exposed():
    assert isinstance(receipt_board.__version__, str)
    assert receipt_board.__version__
