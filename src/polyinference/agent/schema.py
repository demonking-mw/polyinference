"""Render full schema constraints without redundant display titles or whitespace."""

import json


def schema_text(schema):
    def constraints(value):
        if isinstance(value, dict):
            result = {}
            for key, item in value.items():
                if key == "title":
                    continue
                if key in {"properties", "$defs", "patternProperties", "dependentSchemas"}:
                    result[key] = {name: constraints(schema) for name, schema in item.items()}
                elif key in {"const", "enum", "default", "examples"}:
                    result[key] = item
                else:
                    result[key] = constraints(item)
            return result
        if isinstance(value, list):
            return [constraints(v) for v in value]
        return value

    return json.dumps(constraints(schema), separators=(",", ":"))
