# -*- coding: utf-8 -*-

import abc
import os
import subprocess

from typing import Tuple

from .spect_config import (
    TS_REPO_ROOT
)

#############################################################
#   Release Test Helpers
#############################################################
RELEASE_TAG = "TS_SPECT_FW_TEST_RELEASE"
RELEASE_DIR = os.path.join(TS_REPO_ROOT, "release")

def get_release_version():
    try:
        result = subprocess.run(
            ['git', 'describe', '--dirty'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            return output
        else:
            print("Error running 'git describe --dirty' :", result.stderr.strip())
            return None

    except FileNotFoundError:
        print("Git command not found. Make sure Git is installed.")
        return None

class SpectFw(abc.ABC):
    s_file:         str
    hex_file:       str
    const_rom_file: str

    @classmethod
    def check_exists(cls) -> bool:
        return (
            os.path.exists(cls.s_file) and
            os.path.exists(cls.hex_file) and
            os.path.exists(cls.const_rom_file)
        )

    @classmethod
    @abc.abstractmethod
    def get_release_files(cls) -> Tuple[str, str]:
        pass

class SpectDefaultFW:
    class Application(SpectFw):
        s_file = os.path.join(TS_REPO_ROOT, "src", "main.s")
        hex_file = os.path.join(TS_REPO_ROOT, "build", "main.hex")
        const_rom_file = os.path.join(TS_REPO_ROOT, "build", "constants.hex")

        @classmethod
        def get_release_files(cls) -> Tuple[str, str]:
            version = get_release_version()
            constfile = os.path.join(RELEASE_DIR, f"spect_const_rom_code-{version}.hex")
            fw_file = os.path.join(RELEASE_DIR, f"spect_app-{version}.hex")
            return fw_file, constfile


    class Bootloader(SpectFw):
        s_file = os.path.join(TS_REPO_ROOT, "src", "boot_main.s")
        hex_file = os.path.join(TS_REPO_ROOT, "build_boot", "boot_main.hex")
        const_rom_file = os.path.join(TS_REPO_ROOT, "build_boot", "constants.hex")

        @classmethod
        def get_release_files(cls) -> Tuple[str, str]:
            version = get_release_version()
            constfile = os.path.join(RELEASE_DIR, f"spect_const_rom_code-{version}.hex")
            fw_file = os.path.join(RELEASE_DIR, f"spect_boot-{version}.hex")
            return fw_file, constfile
