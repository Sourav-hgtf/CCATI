"""OpenAPI Schema to TypeScript Types Generator Script (TICKET-903).

Extracts OpenAPI JSON schema from FastAPI application and generates type-safe TypeScript interfaces.
"""

import json
from pathlib import Path
from backend.app.main import app

OUTPUT_TS_PATH = Path(__file__).resolve().parent.parent / "frontend" / "src" / "types" / "api.ts"


def generate_typescript_definitions():
    openapi_schema = app.openapi()
    
    components = openapi_schema.get("components", {}).get("schemas", {})
    
    ts_code = [
        "// Auto-generated TypeScript definitions from FastAPI OpenAPI Schema (TICKET-903)",
        "// DO NOT EDIT MANUALLY - Generated via `python scripts/generate_types.py`\n"
    ]

    # Map OpenAPI types to TypeScript types
    type_map = {
        "string": "string",
        "integer": "number",
        "number": "number",
        "boolean": "boolean",
        "array": "any[]",
        "object": "Record<string, any>",
    }

    for schema_name, schema_def in components.items():
        properties = schema_def.get("properties", {})
        required_props = schema_def.get("required", [])

        ts_code.append(f"export interface {schema_name} {{")
        for prop_name, prop_spec in properties.items():
            is_optional = "?" if prop_name not in required_props else ""
            prop_type = prop_spec.get("type", "any")
            
            if "anyOf" in prop_spec or "oneOf" in prop_spec:
                ts_type = "any"
            elif prop_type == "array":
                item_type = prop_spec.get("items", {}).get("type", "any")
                ts_type = f"{type_map.get(item_type, 'any')}[]"
            elif "$ref" in prop_spec:
                ts_type = prop_spec["$ref"].split("/")[-1]
            else:
                ts_type = type_map.get(prop_type, "any")

            ts_code.append(f"  {prop_name}{is_optional}: {ts_type};")
        ts_code.append("}\n")

    OUTPUT_TS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_TS_PATH, "w") as f:
        f.write("\n".join(ts_code))

    print(f"Successfully generated TypeScript definitions at {OUTPUT_TS_PATH}")


if __name__ == "__main__":
    generate_typescript_definitions()
