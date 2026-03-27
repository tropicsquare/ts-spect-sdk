#!/usr/bin/env python3

import yaml
import sys
import os
import argparse
from pathlib import Path
from datetime import date

__author__ = "Vit Masek"
__copyright__ = "Tropic Square s.r.o."
__license___ = "See LICENSE file"
__maintainer__ = "Vit Masek"

def write_op_section_s(s_file, op_name, section_name, items_list, use_base=False):
    """
    Helper function to write a section (input, output, context) of constants.
    """
    # Do nothing if the section is missing or empty
    if not items_list:
        return

    for item in items_list:
        # Use .get() for safe access, defaulting to 0
        addr = item.get("address", 0)

        # Add base address only if specified
        if use_base:
            addr += item.get("base", 0)

        item_name = item.get("name", "UNKNOWN")
        s_file.write(f"{op_name}_{section_name}_{item_name} .eq 0x{addr:X}\n")

def main():
    parser = argparse.ArgumentParser(description='TS SPECT S-File headers generator')
    parser.add_argument("-f", "--file", type=str, default="spect_ops_constants.s",
            help='Destination file name. Default:  "%(default)s"')
    parser.add_argument("-c", "--cfg", type=str, default="spect_ops_config.yml",
            help='Configuration input file name. Default:  "%(default)s"')
    args = parser.parse_args()

    # --- 1. Get Environment Variable ---
    try:
        ts_repo_root = os.environ["TS_REPO_ROOT"]
    except KeyError:
        print("Error: TS_REPO_ROOT environment variable not set.", file=sys.stderr)
        sys.exit(1)

    # --- 2. Setup Paths using pathlib ---
    repo_root_path = Path(ts_repo_root)

    s_file_path = Path(args.file)
    if not s_file_path.is_absolute():
        s_file_path = repo_root_path / s_file_path

    cfg_file_path = Path(args.cfg)
    if not cfg_file_path.is_absolute():
        cfg_file_path = repo_root_path / cfg_file_path

    print(f"Config  -> {cfg_file_path}")
    print(f"Output  -> {s_file_path}")

    # --- 3. Load Config ---
    try:
        with open(cfg_file_path, 'r') as cfg_file:
            cfg = yaml.safe_load(cfg_file)
    except FileNotFoundError:
        print(f"Error: Config file not found at {cfg_file_path}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {cfg_file_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # --- 4. Write Output File ---
    try:
        # Use 'with' to ensure the file is closed automatically
        with open(s_file_path, 'w') as s_file:

            # Write header
            s_file.write(
f"""; ==============================================================================
;   file    {s_file_path.name}
;   author  Tropic Square s.r.o.
;
;  Copyright © {date.today().year} Tropic Square s.r.o. (https://tropicsquare.com/)
;  This work is subject to the license terms of the LICENSE file in the root
;  directory of this source tree.
;  If a copy of the LICENSE file was not distributed with this work, you can
;  obtain one at (https://tropicsquare.com/license).
;
;   generated from {cfg_file_path.name} on {date.today()}
; ==============================================================================
"""
            )

            # Process each operation in the config
            for op in cfg:
                op_name = op.get("name", "UNKNOWN_OP")
                op_id = op.get("id", 0)

                s_file.write(f"\n; {op_name}\n")
                s_file.write(f"{op_name}_id .eq 0x{op_id:02X}\n")

                # Generatge S file
                write_op_section_s(s_file, op_name, "input", op.get("input"), use_base=True)
                write_op_section_s(s_file, op_name, "output", op.get("output"), use_base=True)
                write_op_section_s(s_file, op_name, "context", op.get("context"), use_base=False)

                # Generate C header file

    except IOError as e:
        print(f"Error writing to output file {s_file_path}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
