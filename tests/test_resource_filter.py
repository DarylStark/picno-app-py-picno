"""Tests for the CLI Filter Builder and ResourceFilter."""

import pytest

from picno.model import Image, Label
from picno.resource_filter import FilterBuilder


def test_fields() -> None:
    """Test the `fields` property."""
    parser = FilterBuilder(Image)
    fields = parser.fields

    assert fields['title'] is str
    assert fields['camera_make'] is str
    assert fields['id'] is int
    assert fields['latitude'] is float


@pytest.mark.parametrize('value', ['', '=', '!', '^', '^=', '^!', '^!='])
def test_convert_str_argument_wrong_value(value: str) -> None:
    """Test the "convert_str_argument" method."""
    parser = FilterBuilder(Label)
    with pytest.raises(ValueError):
        parser.convert_str_argument('name', value)


def test_convert_str_argument_any_argument() -> None:
    """Test the "convert_str_argument" method."""
    parser = FilterBuilder(Label)
    converted = parser.convert_str_argument('name', 'test')
    assert converted.field == 'name'
    assert converted.value == 'test'
    assert not converted.is_exact
    assert not converted.is_case_sensitive
    assert not converted.is_negated
    assert not converted.is_all


def test_convert_str_argument_any_argument_exact() -> None:
    """Test the "convert_str_argument" method."""
    parser = FilterBuilder(Label)
    converted = parser.convert_str_argument('name', '=test')
    assert converted.field == 'name'
    assert converted.value == 'test'
    assert converted.is_exact
    assert not converted.is_case_sensitive
    assert not converted.is_negated
    assert not converted.is_all


def test_convert_str_argument_any_argument_case_insensitive() -> None:
    """Test the "convert_str_argument" method."""
    parser = FilterBuilder(Label)
    converted = parser.convert_str_argument('name', '^test')
    assert converted.field == 'name'
    assert converted.value == 'test'
    assert not converted.is_exact
    assert converted.is_case_sensitive
    assert not converted.is_negated
    assert not converted.is_all


def test_convert_str_argument_any_argument_negated() -> None:
    """Test the "convert_str_argument" method."""
    parser = FilterBuilder(Label)
    converted = parser.convert_str_argument('name', '!test')
    assert converted.field == 'name'
    assert converted.value == 'test'
    assert not converted.is_exact
    assert not converted.is_case_sensitive
    assert converted.is_negated
    assert not converted.is_all


def test_convert_str_argument_all_argument() -> None:
    """Test the "convert_str_argument" method."""
    parser = FilterBuilder(Label)
    converted = parser.convert_str_argument('name', 'test', is_all=True)
    assert converted.field == 'name'
    assert converted.value == 'test'
    assert not converted.is_exact
    assert not converted.is_case_sensitive
    assert not converted.is_negated
    assert converted.is_all


def test_convert_str_argument_any_argument_exact_case_sensitive() -> None:
    """Test the "convert_str_argument" method."""
    parser = FilterBuilder(Label)
    converted = parser.convert_str_argument('name', '^=test')
    assert converted.field == 'name'
    assert converted.value == 'test'
    assert converted.is_exact
    assert converted.is_case_sensitive
    assert not converted.is_negated
    assert not converted.is_all


def test_convert_str_argument_any_argument_exact_negated() -> None:
    """Test the "convert_str_argument" method."""
    parser = FilterBuilder(Label)
    converted = parser.convert_str_argument('name', '!=test')
    assert converted.field == 'name'
    assert converted.value == 'test'
    assert converted.is_exact
    assert not converted.is_case_sensitive
    assert converted.is_negated
    assert not converted.is_all


def test_convert_str_argument_any_argument_exact_case_sensitive_negated() -> (
    None
):
    """Test the "convert_str_argument" method."""
    parser = FilterBuilder(Label)
    converted = parser.convert_str_argument('name', '^!=test')
    assert converted.field == 'name'
    assert converted.value == 'test'
    assert converted.is_exact
    assert converted.is_case_sensitive
    assert converted.is_negated
    assert not converted.is_all
