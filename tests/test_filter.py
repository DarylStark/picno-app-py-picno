"""Test for the Filter baseclass."""

from picno.filter_new import FilterNew
from picno.model import Image


def test_filter_construction_for_image() -> None:
    """Test constructing a filter and see if we get the correct fields."""
    filter = FilterNew(model=Image)
    fields = filter.filter_fields

    # Check string fields
    assert 'title' in fields
    assert fields['title'].is_unique
    assert 'camera_model' in fields
    assert not fields['camera_model'].is_unique

    # Check integer fields
    assert 'id' in fields
    assert fields['id'].is_unique
    assert 'width' in fields
    assert not fields['width'].is_unique
    assert 'height' in fields
    assert not fields['height'].is_unique
