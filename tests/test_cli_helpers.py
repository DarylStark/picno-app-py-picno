"""Tests for CLI helpers."""

from typing import Any

import pytest
from sqlmodel import SQLModel

from picno.cli_helpers import FilterParamBuilder
from picno.filter import Filter
from picno.model import Image, Person


def _check_type_annotation(annotation: Any, required: Any) -> bool:  # noqa: ANN401
    return annotation is required or annotation == required


@pytest.mark.parametrize('type', [Image, Person])
def test_filter_param_builder_for_all(type: type[SQLModel]) -> None:
    """Test the Filter Param Builder for images."""
    params = FilterParamBuilder(Filter(type)).fields
    fields = {param.name: param.annotation for param in params}

    assert 'id' in fields
    assert 'id__any' in fields
    assert 'id__ge' in fields
    assert 'id__gt' in fields
    assert 'id__le' in fields
    assert 'id__lt' in fields

    assert _check_type_annotation(fields['id'], int | None)
    assert _check_type_annotation(fields['id__any'], list[int] | None)
    assert _check_type_annotation(fields['id__ge'], int | None)
    assert _check_type_annotation(fields['id__gt'], int | None)
    assert _check_type_annotation(fields['id__le'], int | None)
    assert _check_type_annotation(fields['id__lt'], int | None)


def test_filter_param_builder_for_images() -> None:
    """Test the Filter Param Builder for images."""
    params = FilterParamBuilder(Filter(Image)).fields
    fields = {param.name: param.annotation for param in params}

    assert 'title' in fields
    assert 'title__any' in fields
    assert 'title__ci' in fields
    assert 'title__contains_ci' in fields

    assert _check_type_annotation(fields['title'], str | None)
    assert _check_type_annotation(fields['camera_model'], str | None)
    assert _check_type_annotation(fields['title__any'], list[str] | None)
    assert _check_type_annotation(fields['title__ci'], str | None)
    assert _check_type_annotation(
        fields['title__contains_ci'], list[str] | None
    )


def test_filter_param_builder_for_persons() -> None:
    """Test the Filter Param Builder for persons."""
    params = FilterParamBuilder(Filter(Image)).fields
    fields = {param.name: param.annotation for param in params}

    assert 'title' in fields
    assert 'title__any' in fields
    assert 'title__ci' in fields
    assert 'title__contains_ci' in fields

    assert _check_type_annotation(fields['title'], str | None)
    assert _check_type_annotation(fields['title__any'], list[str] | None)
    assert _check_type_annotation(fields['title__ci'], str | None)
    assert _check_type_annotation(
        fields['title__contains_ci'], list[str] | None
    )
