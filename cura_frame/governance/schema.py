"""A small JSON Schema subset, sufficient for validating a verdict record.

Deliberately not `jsonschema`. This package exists so that recording a verdict
adds no dependency to CuraFrame, and pulling in a validator would defeat that
for the handful of keywords a verdict contract actually uses.

Supported: `type`, `required`, `properties`, `items`, `enum`, `const`,
`minLength`, `minimum`, `maximum`, `minItems`, `maxItems`, and
`additionalProperties: false`. Anything else in a schema is ignored rather than
rejected, so a contract written against the full specification still validates
here -- it is simply checked less strictly than a full validator would check it.

If a contract ever needs more than this, add `jsonschema` and delete the file.
It is 90 lines and owes nothing to its own history.
"""

from __future__ import annotations

from typing import Any

_TYPES: dict[str, type | tuple[type, ...]] = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "integer": int,
    "number": (int, float),
    "null": type(None),
}


class SchemaError(ValueError):
    """Raised when a value does not match the schema it was checked against."""


def _check_type(value: Any, expected: str, path: str) -> None:
    python_type = _TYPES.get(expected)
    if python_type is None:
        return
    # bool is a subclass of int in Python; a schema asking for a number should
    # not silently accept True.
    if expected in ("integer", "number") and isinstance(value, bool):
        raise SchemaError(f"{path}: expected {expected}, got boolean")
    if not isinstance(value, python_type):
        raise SchemaError(f"{path}: expected {expected}, got {type(value).__name__}")


def _check(value: Any, schema: dict[str, Any], path: str) -> None:
    expected = schema.get("type")
    if expected:
        _check_type(value, expected, path)

    if "const" in schema and value != schema["const"]:
        raise SchemaError(f"{path}: expected the constant {schema['const']!r}")

    if "enum" in schema and value not in schema["enum"]:
        raise SchemaError(f"{path}: {value!r} is not one of {schema['enum']}")

    if isinstance(value, str):
        minimum_length = schema.get("minLength")
        if minimum_length is not None and len(value) < minimum_length:
            raise SchemaError(f"{path}: shorter than minLength {minimum_length}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        low, high = schema.get("minimum"), schema.get("maximum")
        if low is not None and value < low:
            raise SchemaError(f"{path}: {value} is below minimum {low}")
        if high is not None and value > high:
            raise SchemaError(f"{path}: {value} is above maximum {high}")

    if isinstance(value, dict):
        for field in schema.get("required", []):
            if field not in value:
                raise SchemaError(f"{path}: missing required field {field!r}")
        properties = schema.get("properties", {})
        for key, item in value.items():
            if key in properties:
                _check(item, properties[key], f"{path}.{key}")
            elif schema.get("additionalProperties", True) is False:
                raise SchemaError(f"{path}: unexpected field {key!r}")

    if isinstance(value, list):
        low, high = schema.get("minItems"), schema.get("maxItems")
        if low is not None and len(value) < low:
            raise SchemaError(f"{path}: fewer than minItems {low}")
        if high is not None and len(value) > high:
            raise SchemaError(f"{path}: more than maxItems {high}")
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, item in enumerate(value):
                _check(item, item_schema, f"{path}[{index}]")


def validate(instance: Any, schema: dict[str, Any], name: str = "record") -> None:
    """Raise `SchemaError` if `instance` does not match `schema`."""
    _check(instance, schema, name)
