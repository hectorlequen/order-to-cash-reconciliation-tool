from order_to_cash.cleaning import is_valid_date


def test_is_valid_date_with_valid_date():
    assert is_valid_date("1789-07-14")


def test_is_valid_date_with_invalid_string():
    assert not is_valid_date("hello world")


def test_is_valid_date_with_invalid_date():
    assert not is_valid_date("2026-30-30")


def test_is_valid_date_with_nan():
    assert not is_valid_date(float("nan"))


def test_is_valid_date_with_none():
    assert not is_valid_date(None)
