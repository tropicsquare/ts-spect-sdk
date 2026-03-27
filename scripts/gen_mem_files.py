#!/usr/bin/env python3

import yaml
import sys
import os
from pathlib import Path
import argparse
from datetime import date

__author__ = "Vit Masek"
__copyright__ = "Tropic Square s.r.o."
__license___ = "See LICENSE file"
__maintainer__ = "Vit Masek"

def main():
    parser = argparse.ArgumentParser(description='TS SPECT Const ROM generator')
    parser.add_argument("-c", "--cfg", type=str, required=True,
            help='Configuration input file name.')
    args = parser.parse_args()

    # --- 1. Get Environment Variable ---
    try:
        ts_repo_root = os.environ["TS_REPO_ROOT"]
    except KeyError:
        print("Error: TS_REPO_ROOT environment variable not set.", file=sys.stderr)
        sys.exit(1)

    # --- 2. Setup Paths ---
    cfg_file_path = Path(args.cfg)
    if not cfg_file_path.is_absolute():
        cfg_file_path = Path(ts_repo_root) / cfg_file_path

    base_name = cfg_file_path.stem
    base_dir = cfg_file_path.parent

    mem_hex_path = base_dir / f"{base_name}.hex32"
    mem_layout_path = base_dir / f"{base_name}_layout.s"

    print(f"Config  -> {cfg_file_path}")
    print(f"Hexfile -> {mem_hex_path}")
    print(f"Layout  -> {mem_layout_path}")

    # --- 3. Load Config and Calculate Size ---
    with open(cfg_file_path, 'r') as cfg_file:
        cfg = yaml.safe_load(cfg_file)

    start_addr = cfg["start_addr"]
    end_addr = cfg["end_addr"]
    mem_size = (end_addr + 1 - start_addr) // 32  # Size in 32-byte slots

    all_items = cfg.get("data", [])
    if len(all_items) > mem_size:
        print(f"Error: Config file data ({len(all_items)} items) exceeds the memory size ({mem_size} slots).", file=sys.stderr)
        print(f"Max size  : {mem_size*32}B")
        print(f"Data size : {len(all_items)*32}B")
        sys.exit(1)

    # --- 4. Process Data (Place Addressed and Unaddressed Items) ---
    data_slots = [None] * mem_size
    unplaced_items = []

    # First pass: place items with fixed addresses
    for item in all_items:
        item.setdefault("value", 0)  # Set default value if missing

        if "address" in item:
            addr = item["address"]

            if addr % 32 != 0:
                print(f"Error: Address for '{item['name']}' (0x{addr:X}) is not 32-byte aligned.", file=sys.stderr)
                sys.exit(1)

            if not (start_addr <= addr <= end_addr):
                print(f"Error: Address for '{item['name']}' (0x{addr:X}) is outside memory range [0x{start_addr:X}, 0x{end_addr:X}].", file=sys.stderr)
                sys.exit(1)

            index = (addr - start_addr) // 32

            if data_slots[index] is not None:
                print(f"Error: Address collision at 0x{addr:X} between '{data_slots[index]['name']}' and '{item['name']}'.", file=sys.stderr)
                sys.exit(1)

            data_slots[index] = item
        else:
            unplaced_items.append(item)

    # Second pass: place remaining items in first-available slots
    slot_iter = 0
    for item in unplaced_items:
        # Find next free slot
        while slot_iter < mem_size and data_slots[slot_iter] is not None:
            slot_iter += 1

        if slot_iter == mem_size:
            print(f"Error: Not enough space in memory to place unaddressed item '{item['name']}'.", file=sys.stderr)
            sys.exit(1)

        # Assign address and place item
        addr = start_addr + slot_iter * 32
        item["address"] = addr
        data_slots[slot_iter] = item

    # --- 5. Write Output Files ---
    try:
        with open(mem_hex_path, "w") as f_hex, open(mem_layout_path, "w") as f_layout:
            # Write layout header
            f_layout.write(
f"""; ==============================================================================
;   file    mem_layouts/{mem_layout_path.name}
;   author  Tropic Square s.r.o.
;
;  Copyright © {date.today().year} Tropic Square s.r.o. (https://tropicsquare.com/)
;  This work is subject to the license terms of the LICENSE file in the root
;  directory of this source tree.
;  If a copy of the LICENSE file was not distributed with this work, you
;  obtain one at (https://tropicsquare.com/license)
;
;   generated from {cfg_file_path.name}
; ==============================================================================
"""
            )

            # Write data for both files
            for item in data_slots:
                if item is None:
                    # Empty slot
                    value = 0
                else:
                    # Filled slot
                    value = item["value"]
                    # Write layout entry
                    f_layout.write(f"{item['name']} .eq 0x{item['address']:04X}\n")

                # Write 8 32-bit (4-byte) words to hex file (total 32 bytes)
                for i in range(8):
                    word = (value >> (i * 32)) & 0xFFFFFFFF
                    f_hex.write(f"{word:08X}\n")

    except IOError as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
