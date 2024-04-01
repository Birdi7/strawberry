from __future__ import annotations

from typing import Any

import pytest

import strawberry
from strawberry.schema_directives import OneOf


@strawberry.input(directives=[OneOf()])
class ExampleInputTagged:
    a: str | None
    b: int | None


@strawberry.type
class ExampleResult:
    a: str | None
    b: int | None


@strawberry.type
class Query:
    @strawberry.field
    def test(self, input: ExampleInputTagged) -> ExampleResult:
        return input  # type: ignore


schema = strawberry.Schema(query=Query)


@pytest.mark.parametrize(
    ("default_value", "variables"),
    (
        ("{a: null, b: null}", {}),
        ('{ a: "abc", b: 123 }', {}),
        ("{a: null, b: 123}", {}),
        ("{}", {}),
    ),
)
def test_must_specify_at_least_one_key_default(
    default_value: str, variables: dict[str, Any]
):
    query = f"""
        query ($input: ExampleInputTagged! = {default_value}) {{
          test(input: $input) {{
            a
            b
          }}
        }}
    """

    result = schema.execute_sync(query, variable_values=variables)

    assert result.errors
    assert len(result.errors) == 1
    assert (
        result.errors[0].message
        == "OneOf Input Object 'ExampleInputTagged' must specify exactly one key."
    )


@pytest.mark.parametrize(
    ("value", "variables"),
    [
        ("{a: null, b: null}", {}),
        ('{ a: "abc", b: 123 }', {}),
        ("{a: null, b: 123}", {}),
        ("{}", {}),
        ("{ a: $a, b: 123 }", {"a": "abc"}),
        ("{ a: $a, b: 123 }", {}),
        ("{ a: $a, b: $b }", {"a": "abc"}),
        ("$input", {"input": {"a": "abc", "b": 123}}),
        ("$input", {"input": {"a": "abc", "b": None}}),
        ("$input", {"input": {}}),
        ('{ a: "abc", b: null }', {}),
    ],
)
def test_must_specify_at_least_one_key_literal(value: str, variables: dict[str, Any]):
    variables_definitions = []

    if "$a" in value:
        variables_definitions.append("$a: String")

    if "$b" in value:
        variables_definitions.append("$b: Int")

    if "$input" in value:
        variables_definitions.append("$input: ExampleInputTagged!")

    variables_definition_str = (
        f'({", ".join(variables_definitions)})' if variables_definitions else ""
    )

    query = f"""
        query {variables_definition_str} {{
          test(input: {value}) {{
            a
            b
          }}
        }}
    """

    result = schema.execute_sync(query, variable_values=variables)

    assert result.errors
    assert len(result.errors) == 1
    assert (
        result.errors[0].message
        == "OneOf Input Object 'ExampleInputTagged' must specify exactly one key."
    )


@pytest.mark.parametrize(
    ("value", "variables", "key"),
    [
        ("{ a: null }", {}, "a"),
        ("{ b: $b }", {"b": None}, "b"),
        ("$input", {"input": {"a": None}}, "a"),
    ],
)
def test_value_must_be_non_null(value: str, variables: dict[str, Any], key: str):
    variables_definitions = []

    if "$a" in value:
        variables_definitions.append("$a: String")

    if "$b" in value:
        variables_definitions.append("$b: Int")

    if "$input" in value:
        variables_definitions.append("$input: ExampleInputTagged!")

    variables_definition_str = (
        f'({", ".join(variables_definitions)})' if variables_definitions else ""
    )

    query = f"""
        query {variables_definition_str} {{
          test(input: {value}) {{
            a
            b
          }}
        }}
    """

    result = schema.execute_sync(query, variable_values=variables)

    assert result.errors
    assert len(result.errors) == 1
    assert (
        result.errors[0].message == f"Value for member field '{key}' must be non-null"
    )


@pytest.mark.parametrize(
    ("value", "variables", "expected"),
    [
        ("{ b: $b }", {"b": 123}, {"b": 123}),
        ("$input", {"input": {"b": 123}}, {"b": 123}),
        ('{ a: "abc" }', {}, {"a": "abc"}),
        ("$input", {"input": {"a": "abc"}}, {"a": "abc"}),
    ],
)
def test_works(value: str, variables: dict[str, Any], expected: dict[str, Any]):
    variables_definitions = []

    if "$a" in value:
        variables_definitions.append("$a: String")

    if "$b" in value:
        variables_definitions.append("$b: Int")

    if "$input" in value:
        variables_definitions.append("$input: ExampleInputTagged!")

    variables_definition_str = (
        f'({", ".join(variables_definitions)})' if variables_definitions else ""
    )

    field = next(iter(expected.keys()))

    query = f"""
        query {variables_definition_str} {{
          test(input: {value}) {{
            {field}
          }}
        }}
    """

    result = schema.execute_sync(query, variable_values=variables)

    assert not result.errors
    assert result.data["test"] == expected