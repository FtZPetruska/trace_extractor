#  Copyright (C) 2022  Pierre Wendling
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Entry point of the program. Parses arguments and checks input files."""

import argparse
import enum
import os
from typing import Optional

from . import data_extract
from . import data_transform
from .logger import disable_logging, log


class ReturnValue(enum.IntEnum):
    """Definition of all possible return values"""
    SUCCESS = 0b0000
    NO_VALID_FILE = 0b0001
    FFPROBE_NOT_FOUND = 0b0010
    FFPROBE_ERROR = 0b0100
    TRANSFORM_ERROR = 0b1000


def _parse_args() -> tuple[list[str], Optional[str]]:
    """Parses the given arguments."""
    parser = argparse.ArgumentParser(
        description="MPEG-4 video trace extractor for ns-3.")
    parser.add_argument("input", metavar="input.mp4",
                        nargs='*', help="The input file(s)")
    parser.add_argument("--disable-logging", dest="disable_logging",
                        action="store_true", required=False,
                        default=False, help="Disable logging")
    parser.add_argument("--ffprobe-path", dest="ffprobe_path",
                        action="store", required=False,
                        default=None, help="Path to the ffprobe binary")
    args = parser.parse_args()
    if args.disable_logging:
        disable_logging()
    return args.input, args.ffprobe_path


def _get_filenames_from_input_dir() -> list[str]:
    """Checks the input directory for MPEG-4 files."""
    input_dir = os.path.join(os.path.curdir, "input")
    if not os.path.isdir(input_dir):
        log.warning("The path %s does not exist.", input_dir)
        return []

    return [os.path.join(input_dir, file) for file in os.listdir(input_dir)]


def _dedupe_filenames(filenames: list[str]) -> list[str]:
    """Removes files that appear twice and with the same name."""
    deduped_filenames: list[str] = []

    for candidate_file in filenames:
        accepted = True
        candidate_base = os.path.basename(candidate_file)

        for chosen_file in deduped_filenames:

            if os.path.samefile(candidate_file, chosen_file) and accepted:
                accepted = False
                log.warning(
                    "Files %s and %s are the same, "
                    "only the first will be processed.",
                    chosen_file, candidate_file)

            if os.path.basename(chosen_file) == candidate_base and accepted:
                accepted = False
                log.warning(
                    "Files %s and %s have the same name, "
                    "only the first will be processed.",
                    chosen_file, candidate_file)

        if accepted:
            deduped_filenames.append(candidate_file)
    return deduped_filenames


def _filter_filenames(filenames: list[str]) -> list[str]:
    """Checks for the correct file extension and for existence."""
    filtered_filenames: list[str] = []
    for file in filenames:
        accepted = True

        if not file.lower().endswith(".mp4") and accepted:
            accepted = False
            log.warning(
                "File %s does not ends with .mp4 and has been removed.", file)

        if not os.path.exists(file) and accepted:
            accepted = False
            log.warning("File %s does not exist and has been removed.", file)

        if accepted:
            filtered_filenames.append(file)

    return filtered_filenames


def entry_point() -> int:
    """Program's entry point"""
    ret_val: int = ReturnValue.SUCCESS

    raw_filenames, ffprobe_path = _parse_args()
    if not data_extract.is_ffprobe_available(ffprobe_path):
        log.error("FFProbe could not be found.")
        return ReturnValue.FFPROBE_NOT_FOUND

    raw_filenames += _get_filenames_from_input_dir()

    if not raw_filenames:
        log.error("No files were given, use --help for help.")
        return ReturnValue.NO_VALID_FILE

    filtered_filenames = _filter_filenames(raw_filenames)
    deduped_filenames = _dedupe_filenames(filtered_filenames)

    if not deduped_filenames:
        log.error("No valid files are left.")
        return ReturnValue.NO_VALID_FILE

    for filename in deduped_filenames:
        json_data = data_extract.get_data_from_file(filename)
        if not json_data:
            log.error("FFProbe produced no output for file %s, "
                      "please ensure this is a valid MPEG-4 file.",
                      filename)
            ret_val |= ReturnValue.FFPROBE_ERROR
            continue

        if not data_transform.transform_data(json_data,
                                             os.path.basename(filename)):
            log.error("The data transformation failed for file %s",
                      filename)
            ret_val |= ReturnValue.TRANSFORM_ERROR

    return ret_val