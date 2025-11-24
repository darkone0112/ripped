from ripped.main import format_quality_label


def test_format_quality_label_max():
    assert format_quality_label(None) == "max"


def test_format_quality_label_number():
    assert format_quality_label(720) == "720"
