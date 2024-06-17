import argparse
import json
from dataclasses import dataclass
from typing import List

import common


@dataclass
class SchemaParameter:
    name: str
    type: str
    description: str


@dataclass
class DefinitionReference:
    name: str
    anchor: str


@dataclass
class DefinitionFieldDescription:
    field_name: str
    description: str


@dataclass
class SchemaDefinition:
    name: str
    schema: str
    references: List[DefinitionReference]
    descriptions: List[DefinitionFieldDescription]


def remove_schema_props(node):
    if type(node) is dict:
        return {key: remove_schema_props(item) for key, item in node.items() if key != "$schema"}
    else:
        return node


def presentable_top_node(top_node):
    without_defs = {key: item for key, item in top_node.items() if key not in ["definitions"]}
    return json.dumps(without_defs, indent=4)


def extract_ref_name_and_anchor(ref):
    prefix = "#/$defs/"
    if ref.startswith(prefix):
        name = ref[len(prefix) :]
    return name, name.lower()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Backend JSON documentation")
    parser.add_argument("--input", type=str, help="input json file generated by the json schema generator")
    parser.add_argument("--output", type=str, help="output file")
    parser.add_argument("--template", type=str, help="template")
    args = parser.parse_args()

    json_schema_file = open(args.input)
    json_top_node = json.load(json_schema_file)
    json_schema_file.close()

    json_top_node = remove_schema_props(json_top_node)

    parameters = []
    for name, prop in json_top_node["properties"].items():
        if "$ref" in prop:
            ref_name, ref_anchor = extract_ref_name_and_anchor(prop["$ref"])
            parameters.append(SchemaParameter(name, "$ref", f"Please see [{ref_name}](#{ref_anchor})"))
        else:
            parameters.append(SchemaParameter(name, prop["type"], ""))

    definitions = []
    definitions.sort(key=lambda d: d.name)

    for name, definition in json_top_node["$defs"].items():
        references = []
        descriptions = []
        for prop_name, prop in definition.get("properties", {}).items():
            if "$ref" in prop:
                ref_name, ref_anchor = extract_ref_name_and_anchor(prop["$ref"])
                references.append(DefinitionReference(ref_name, ref_anchor))
            if "description" in prop:
                descriptions.append(DefinitionFieldDescription(prop_name, prop["description"]))

        definitions.append(SchemaDefinition(name, presentable_top_node(definition), references, descriptions))

    presentable_json = presentable_top_node(json_top_node)

    output_file = open(args.output, "w")
    print(
        common.fill_template(
            args.template, event_schema=presentable_json, parameters=parameters, definitions=definitions
        ),
        file=output_file,
    )
    output_file.close()
