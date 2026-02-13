#!/usr/bin/env python3
"""Extract text content from .docx files in the inbox."""

import sys
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

def extract_docx_text(docx_path):
    """Extract plain text from a .docx file."""
    try:
        with zipfile.ZipFile(docx_path) as zip_ref:
            with zip_ref.open('word/document.xml') as xml_file:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Namespace for Word XML
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

                # Extract all text elements
                texts = []
                for text_elem in root.findall('.//w:t', ns):
                    if text_elem.text:
                        texts.append(text_elem.text)

                return ''.join(texts)
    except Exception as e:
        return f"ERROR: {e}"

if __name__ == "__main__":
    inbox = Path("f:/DnD-3.5/inbox")
    output_dir = inbox / "extracted"
    output_dir.mkdir(exist_ok=True)

    for docx_file in sorted(inbox.glob("*.docx")):
        text = extract_docx_text(docx_file)
        output_file = output_dir / f"{docx_file.stem}.txt"
        output_file.write_text(text, encoding='utf-8')
        print(f"Extracted: {docx_file.name} -> {output_file.name}")
