#!/usr/bin/env python3
import zipfile
from importlib import resources
import os

OUTPUT_DIR = ""

def unzip_example(output_dir: str):
    package_name = 'midiUtils.data.zippedSeedExamples'
    resource_name = 'trialExamples.zip'

    # Ensure the target directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Use importlib.resources to access the zip file
    with resources.path(package_name, resource_name) as zip_path:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
            print(f"Unzipped {resource_name} to {output_dir}")

if __name__ == "__main__":
    unzip_example(OUTPUT_DIR)