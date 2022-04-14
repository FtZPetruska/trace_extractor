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
"""Provides a class to extract frames data from a MPEG-4 video file
using ffprobe.
"""

import json
import os
import shutil
import subprocess


class Ffprobe:
    """Manager for the ffprobe executable"""

    def __init__(self) -> None:
        self._ffprobe_path = "ffprobe"

    def set_custom_path(self, path) -> None:
        """Set the path to the ffprobe executable"""
        self._ffprobe_path = path

    def get_ffprobe_path(self) -> str:
        """Get the path to the ffprobe executable."""
        return self._ffprobe_path


class DataExtractor:
    """Extract frame data using ffprobe"""
    ffprobe_executable = Ffprobe()

    def __init__(self, input_filename) -> None:
        self._input_filename = input_filename

    def _call_ffprobe(self) -> bytes:
        ffprobe_args = [
            self.ffprobe_executable.get_ffprobe_path(),
            "-select_streams",
            "v:0",
            "-print_format",
            "json=compact=1",
            "-show_frames",
            self._input_filename
        ]
        try:
            proc = subprocess.run(ffprobe_args, check=True,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            result = b""
        else:
            result = proc.stdout
        return result

    def _try_load_json_data(self, ffprobe_stdout: bytes) -> dict:
        try:
            json_data = json.loads(ffprobe_stdout)
        except json.JSONDecodeError:
            json_data = {}
        return json_data

    def run(self) -> dict:
        """Calls ffprobe and returns the json data."""
        raw_data = self._call_ffprobe()
        return self._try_load_json_data(raw_data)


def is_ffprobe_available(executable_path: str) -> bool:
    """Checks if the given ffprobe path is valid, otherwise check for it
    in PATH.
    """
    if os.path.exists(executable_path):
        DataExtractor.ffprobe_executable.set_custom_path(executable_path)
    return shutil.which(DataExtractor.ffprobe_executable.get_ffprobe_path())\
        is not None
