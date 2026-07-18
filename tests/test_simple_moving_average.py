import pytest

from app.technical_indicators import (
    simple_moving_average,
)


def test_calculates_average_for_requested_period() -> None:
    result = simple_moving_average(
        values=[
            10.0,
            12.0,
            14.0,
            16.0,
        ],
        period=3,
    )

    assert result == pytest.approx(
        14.0
    )