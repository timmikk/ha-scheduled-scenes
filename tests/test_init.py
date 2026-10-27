"""Smoke test — the module imports."""


def test_import():
    """The integration package can be imported."""
    from custom_components import scheduled_scenes  # noqa: F401
