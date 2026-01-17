import os
from lxml import etree
from pathlib import Path

p = Path(__file__).parents[0]

def escape_newlines(value: str) -> str:
    """
    Convert real newline characters to literal "\n"
    so the output matches the original JSON exactly.
    """
    return value.replace("\n", "\\n")

def parse_xml_recursive(element, prefix, keys_list, values_list):
    for child in element:
        if child.tag == "category":
            name = child.get("name")
            parse_xml_recursive(child, prefix + [name], keys_list, values_list)

        elif child.tag == "item":
            name = child.get("name")
            value = child.text if child.text else ""

            # Normalize to literal \n for safe storage
            value = escape_newlines(value)

            key = ";".join(prefix + [name])
            keys_list.append(key)
            values_list.append(value)

def xml_to_txt_files(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    for file_name in os.listdir(input_folder):
        if not file_name.endswith(".xml"):
            continue

        xml_path = os.path.join(input_folder, file_name)
        lang_name = file_name[:-4]

        tree = etree.parse(xml_path)
        root = tree.getroot()

        keys_list = []
        values_list = []

        parse_xml_recursive(root, [lang_name], keys_list, values_list)

        target_dir = os.path.join(output_folder, lang_name)
        os.makedirs(target_dir, exist_ok=True)

        # Write ID.txt
        with open(os.path.join(target_dir, "ID.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(keys_list))

        # Write value.txt (escaped newlines preserved)
        with open(os.path.join(target_dir, "value.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(values_list))

        print(f"TXT files saved to {target_dir}")

# Example usage
input_folder = os.path.join(p, "cs")
output_folder = os.path.join(p, "cs_txt")
xml_to_txt_files(input_folder, output_folder)
