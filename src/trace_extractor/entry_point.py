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
import dataclasses
import enum
import os
import threading

from .data_extract import DataExtractor, is_ffprobe_available
from .data_transform import DataTransformer
from .input_file_sanitizing import InputFilesSanitiser
from .logger import enable_info_logging, log


class ReturnValue(enum.IntEnum):
    """Definition of all possible return values"""
    SUCCESS = 0b0000
    NO_VALID_FILE = 0b0001
    FFPROBE_NOT_FOUND = 0b0010
    FFPROBE_ERROR = 0b0100
    TRANSFORM_ERROR = 0b1000


@dataclasses.dataclass
class Arguments:
    """Represents the program's arguments"""
    input_files: list[str] = []
    verbose_logging: bool = False
    ffprobe_executable: str = ""


def _parse_args(argv: list[str]) -> Arguments:
    parser = argparse.ArgumentParser(
        description="MPEG-4 video trace extractor for ns-3.")
    parser.add_argument(dest="input_files", metavar="input.mp4",
                        nargs='*', help="The input file(s)")
    parser.add_argument("-v", "--verbose", dest="verbose_logging",
                        action="store_true", required=False,
                        default=False, help="Enables verbose output")
    parser.add_argument("--ffprobe-path", dest="ffprobe_path",
                        action="store", required=False,
                        default="", help="Path to the ffprobe binary")
    args = parser.parse_args(argv)
    return Arguments(input_files=args.input_files,
                     verbose_logging=args.verbose_logging,
                     ffprobe_executable=args.ffprobe_path)


class EntryPoint:
    """Defines the program's entry point."""

    _lock = threading.Lock()

    def __init__(self, argv: list[str]) -> None:
        self._return_value: int = ReturnValue.SUCCESS
        self._arguments = _parse_args(argv)
        self._input_filenames = self._arguments.input_files

    def _process_args(self) -> bool:
        """Disables logging if requested and checks for ffprobe availability.

        Returns False if ffprobe is not available.
        """
        if self._arguments.verbose_logging:
            enable_info_logging()

        return is_ffprobe_available(self._arguments.ffprobe_executable)

    def _parse_input_directory(self) -> None:
        """Checks the input directory files."""
        input_dir = os.path.join(os.path.curdir, "input")
        if not os.path.isdir(input_dir):
            log.warning("The path %s does not exist.", input_dir)
        else:
            files = os.listdir(input_dir)
            files.remove(".gitignore")
            self._input_filenames.extend([
                os.path.join(input_dir, file) for file in files])

    def _worker_thread(self, filename: str) -> None:
        log.info("Starting work on '%s'.", filename)
        json_data = DataExtractor(filename).run()
        if not json_data:
            log.error("FFProbe produced no output for file %s, "
                      "please ensure this is a valid MPEG-4 file.",
                      filename)
            with self._lock:
                self._return_value |= ReturnValue.FFPROBE_ERROR
            return

        if not DataTransformer(json_data, os.path.basename(filename)).run():
            log.error("The data transformation failed for file %s",
                      filename)
            with self._lock:
                self._return_value |= ReturnValue.TRANSFORM_ERROR
            return
        log.info("Finished work on '%s'.", filename)

    def _spread_work(self, sanitized_filenames: list[str]) -> None:
        """Spreads the work between multiple threads."""
        threads: list[threading.Thread] = []
        for filename in sanitized_filenames:
            thread = threading.Thread(target=self._worker_thread,
                                      args=(filename,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    def run(self) -> int:
        """Starts the program."""
        if not self._process_args():
            log.error("ffprobe executable could not be found.")
            return ReturnValue.FFPROBE_NOT_FOUND

        self._parse_input_directory()

        if not self._input_filenames:
            log.error("No files were given, use --help for help.")
            return ReturnValue.NO_VALID_FILE

        sanitized_filenames = InputFilesSanitiser(self._input_filenames).run()

        if not sanitized_filenames:
            log.error("No valid files are left.")
            return ReturnValue.NO_VALID_FILE

        self._spread_work(sanitized_filenames)

        return self._return_value
