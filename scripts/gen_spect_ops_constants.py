#!/usr/bin/env python3

import yaml
import sys
import os

import argparse

parser = argparse.ArgumentParser(description='TS SPECT headers generator')

parser.add_argument("-f", "--file", type=str, default="spect_ops_constants.s",
        help='Destination file name. Default:  "%(default)s"')

parser.add_argument("-c", "--cfg", type=str, default="spect_ops_config.yml",
        help='Configuration input file name. Default:  "%(default)s"')

args = parser.parse_args()

TS_REPO_ROOT = os.environ["TS_REPO_ROOT"]

s_file_name = args.file
if not os.path.isabs(s_file_name):
    s_file_name = os.path.join(TS_REPO_ROOT, s_file_name)

cfg_file_name = args.cfg
if not os.path.isabs(cfg_file_name):
    cfg_file_name = os.path.join(TS_REPO_ROOT, cfg_file_name)


with open(cfg_file_name, 'r') as cfg_file:
    cfg = yaml.safe_load(cfg_file)

s_file = open(s_file_name, 'w')

s_file.write(
    "; ==============================================================================\n"
    ";   file    constants/spect_ops_constants.s\n"
    ";   author  tropicsquare s. r. o.\n"
    ";\n"
    ";  Copyright © 2023 Tropic Square s.r.o. (https://tropicsquare.com/)            \n"
    ";  This work is subject to the license terms of the LICENSE.txt file in the root\n"
    ";  directory of this source tree.                                               \n"
    ";  If a copy of the LICENSE file was not distributed with this work, you can    \n"
    ";  obtain one at (https://tropicsquare.com/license).                            \n"
    ";\n"
    f";   generated from {args.cfg}.yml\n"
    "; ==============================================================================\n"
)

for op in cfg:
    s_file.write("; " + op["name"] + '\n' )
    s_file.write("{} .eq 0x{}\n".format(op["name"]+"_id", format(op["id"], '02X')))
    if "input" in op.keys() and op["input"]:
        for input in op["input"]:
            addr = input["address"]
            if "base" in input.keys() and input["base"]:
                addr += input["base"]
            s_file.write("{} .eq 0x{}\n".format(op["name"]+"_input_"+input["name"], format(addr, 'X')))
    if "output" in op.keys() and op["output"]:
        for output in op["output"]:
            addr = output["address"]
            if "base" in output.keys() and output["base"]:
                addr += output["base"]
            s_file.write("{} .eq 0x{}\n".format(op["name"]+"_output_"+output["name"], format(addr, 'X')))
    if "context" in op.keys() and op["context"]:
        for context in op["context"]:
            s_file.write("{} .eq 0x{}\n".format(op["name"]+"_context_"+context["name"], format(context["address"], 'X')))

s_file.close()
