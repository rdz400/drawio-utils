#!/usr/bin/env python3
"""Verwerk XML-objecten afkomstig uit draw.io diagrammen.
"""

import xml
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

################################################################################
# Useful helpers
################################################################################


def xml_attributes_to_dict(
    element: xml.etree.ElementTree.Element,
    attributes,
) -> dict:
    """Get XLM element attributes and return as dict."""
    return {attrib: element.attrib.get(attrib, None) for attrib in attributes}


def child_or_none(
    element: xml.etree.ElementTree.Element,
    child_tag: str,
) -> None | xml.etree.ElementTree.Element:
    """Return the first child with tag `child_tag` or None if not present."""
    children_element = [*element.iter(child_tag)]
    if len(children_element) > 0:
        return children_element[0]  # Return the first one
    return None  # Let's be explicit about it


def merge_dicts_prefer_not_none(a: dict, b: dict, /) -> dict:
    """Merge a and b, prefer a over b although None values get deprioritized."""

    new_dict = {}
    for key in a.keys() | b.keys():
        if key in a:
            if a[key] is None:
                assign = b.get(key)  # Try b and fallback to None
            else:
                assign = a[key]
        else:  # if not in a it must be in b
            assign = b[key]
        new_dict[key] = assign
        del assign
    return new_dict


################################################################################
# Object parsers start here
# Probably could create one generic class/function instead of all these ones
################################################################################


def parse_object(element: xml.etree.ElementTree.Element) -> dict:
    """Extract attributes from a draw.io object element."""

    # Ensure the correct input
    if element.tag != "object":
        raise ValueError(f"Element should be of type 'object' not {element.tag!r}")

    # What we want to get
    attribs_to_fetch = ["label", "id", "tags"]  # for now ignore custom props
    object_attribs = xml_attributes_to_dict(element, attribs_to_fetch)

    if (mx_cell := child_or_none(element, "mxCell")) is not None:
        mx_cell_attribs = parse_mxcell(mx_cell)
    else:
        mx_cell_attribs = {}

    # return mx_cell_attribs | object_attribs
    return merge_dicts_prefer_not_none(object_attribs, mx_cell_attribs)


def parse_mxcell(element: xml.etree.ElementTree.Element) -> dict:
    """Extract attributes from a draw.io mxCell element."""

    # Ensure the correct input
    if element.tag != "mxCell":
        raise ValueError(f"Element should be of type 'mxCell' not {element.tag!r}")

    # What we want to get
    attribs_to_fetch = ["value", "style", "id", "parent", "vertex"]
    mxcell_attribs = xml_attributes_to_dict(element, attribs_to_fetch)

    # Possibly process mxGeometry if contained
    if (mxgeo := child_or_none(element, "mxGeometry")) is not None:
        mxgeo_attribs = parse_mxgeo(mxgeo)
    else:
        mxgeo_attribs = {}

    # return mxgeo_attribs | mxcell_attribs
    return merge_dicts_prefer_not_none(mxcell_attribs, mxgeo_attribs)


def parse_mxgeo(element: xml.etree.ElementTree.Element) -> dict:
    """Extract attributes from a draw.io mxGeometry element."""

    if element.tag != "mxGeometry":
        raise ValueError(f"Element should be of type 'mxGeometry' not {element.tag!r}")

    # What we want
    attribs_to_fetch = ["x", "y", "width", "height"]
    mx_geo_attribs = xml_attributes_to_dict(element, attribs_to_fetch)

    return mx_geo_attribs


def parse_userobject(element: xml.etree.ElementTree.Element) -> dict:
    """Extract attributes from a draw.io UserObject element."""

    # Ensure the correct input
    if element.tag != "UserObject":
        raise ValueError(f"Element should be of type 'UserObject' not {element.tag!r}")

    attribs_to_fetch = ["label", "tags", "id"]
    mx_user_object = xml_attributes_to_dict(element, attribs_to_fetch)

    # If mxCell is contained parse that as well
    if (mx_cell := child_or_none(element, "mxCell")) is not None:
        mx_cell_attribs = parse_mxcell(mx_cell)
    else:
        mx_cell_attribs = {}

    # return mx_cell_attribs | mx_user_object
    return merge_dicts_prefer_not_none(mx_user_object, mx_cell_attribs)


################################################################################
# Representation of a drawio element
################################################################################


@dataclass
class DrawioElement:
    """Node from a draw.io diagram"""

    id: str
    value: str | None = None
    label: str | None = None
    tags: str | None = None
    style: str | None = None
    parent: str | None = None
    value: str | None = None
    vertex: str | None = None
    x: str | None = None
    y: str | None = None
    width: str | None = None
    height: str | None = None


def parse_diagram(diagram: Path) -> list[DrawioElement]:
    """Parse a drawio file and return the shapes as a list of DrawioElements"""

    # Create a tree from the diagram file and get the root element
    tree = ET.parse(diagram)
    root = tree.getroot()

    # Find all children that represent shapes on the diagram
    child_shapes = root.findall("./diagram[1]/mxGraphModel/root/*")

    # Allocate parsers to tag names
    parser = {
        "object": parse_object,
        "mxCell": parse_mxcell,
        "UserObject": parse_userobject,
    }

    # Gather the shapes and fill our list with instances
    data = []
    for shape in child_shapes:
        # Parse the shape and instantiate an DrawioElement object
        data.append(DrawioElement(**parser[shape.tag](shape)))

    return data


def tabulate_data(data: list[DrawioElement]):
    """Show data as a pandas dataframe"""
    import pandas as pd
    import numpy as np

    df = pd.DataFrame(data)
    df = (
        df
        .assign(
            content=lambda df: np.where(pd.isna(df['label']), df['value'], df['label'])
            )

    )
    return df


def main():
    """Entrypoint to process files from the command line"""

    import argparse

    parser = argparse.ArgumentParser(description="Parse drawio diagrams")

    parser.add_argument("files", nargs="+", action="store", type=Path)
    # parser.add_argument("-f", "--file", nargs="+", action="store")
    args = parser.parse_args()

    # file, *_ = args.files

    for file in args.files:
        print(f"== Processing {file}")
        data = parse_diagram(file)
        df = tabulate_data(data)
        print(df.loc[:, ['id', 'content', 'style']])
    # print(df.loc[:, ['id', 'label', 'value', 'style', 'parent']].to_markdown())


if __name__ == "__main__":
    main()
