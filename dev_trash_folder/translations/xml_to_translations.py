import os
import json
from lxml import etree
from pathlib import Path

p = Path(__file__).parents[0]

def parse_xml_recursive(element, prefix, results):
    """
    Recursively walks XML structure and reconstructs keys.
    """
    for child in element:
        if child.tag == "category":
            name = child.get("name")
            parse_xml_recursive(child, prefix + [name], results)

        elif child.tag == "item":
            name = child.get("name")
            value = child.text if child.text else ""
            key = ";".join(prefix + [name])
            results[key] = value

def xml_to_json_folder(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    for file_name in os.listdir(input_folder):
        if not file_name.endswith(".xml"):
            continue

        xml_path = os.path.join(input_folder, file_name)
        lang_name = file_name[:-4] + "_lang"  # reverse of foldername[0:-5]

        tree = etree.parse(xml_path)
        root = tree.getroot()

        results = {}

        # Extract all nested categories/items
        parse_xml_recursive(root, [lang_name], results)

        # Create output folder and write JSON
        target_dir = os.path.join(output_folder, lang_name)
        os.makedirs(target_dir, exist_ok=True)

        json_path = os.path.join(target_dir, "en.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

        print(f"JSON output saved to {json_path}")

# Example usage
input_folder = os.path.join(p, "cs")
output_folder = os.path.join(p, "cs_json")
xml_to_json_folder(input_folder, output_folder)
