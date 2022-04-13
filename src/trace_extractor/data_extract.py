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
"""Provides functions to extract frames data from a MPEG-4 video file
using ffprobe.
"""

import json
import os
import subprocess
import shutil
from typing import Optional


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


_FFPROBE = Ffprobe()


def is_ffprobe_available(executable_path: Optional[str] = None) -> bool:
    """Checks if the given ffprobe path is valid, otherwise check for it
    in PATH.
    """
    if executable_path is not None and os.path.exists(executable_path):
        _FFPROBE.set_custom_path(executable_path)
    return shutil.which(_FFPROBE.get_ffprobe_path()) is not None


def _call_ffprobe(file: str) -> bytes:
    """Launches the ffprobe subprocess.

    Returns the content of stdout if successful.
    """
    ffprobe_args = [
        _FFPROBE.get_ffprobe_path(),
        "-select_streams",
        "v:0",
        "-print_format",
        "json=compact=1",
        "-show_frames",
        file
    ]
    try:
        proc = subprocess.run(ffprobe_args, check=True, stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        result = b""
    else:
        result = proc.stdout
    return result


def get_data_from_file(file: str) -> dict:
    """Calls ffprobe with the given file and returns the raw JSON data."""
    raw_data = _call_ffprobe(file)
    try:
        json_data = json.loads(raw_data)
    except json.JSONDecodeError:
        json_data = {}
    return json_data
