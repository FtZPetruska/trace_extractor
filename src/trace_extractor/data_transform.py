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
"""Converts ffprobe's output into a file readable by ns3's UdpTraceClient"""

import math
import os

from .logger import log


class DataTransformer:
    """Transform the raw ffprobe data into a format readable by ns-3:

    `<frame index> <frame type> <frame time (ms, integer)> <frame size>`
    """
    _output_directory = os.path.join(os.path.curdir, "output")

    def __init__(self, json_data: dict, input_file_basename: str) -> None:
        self._json_data = json_data
        self._file_basename = input_file_basename
        self._output_filename = self._get_output_filename()
        self._ensure_output_directory_exists()

    def _ensure_output_directory_exists(self) -> None:
        """Checks if the output directory exists, create it otherwise."""
        if not os.path.isdir(self._output_directory):
            os.mkdir(self._output_directory)

    def _get_output_filename(self) -> str:
        """Obtain the output file name based on the input file."""
        output_extension = "ns-3-vtrace"
        filename, _ = os.path.splitext(self._file_basename)
        return os.path.join(
            self._output_directory,
            '.'.join((filename, output_extension))
        )

    def _convert_data(self) -> str:

        transformed_data: list[str] = []

        frames = self._json_data["frames"]

        for frame in frames:
            frame_number = frame["coded_picture_number"]
            frame_type = frame["pict_type"]
            frame_time_s = frame["pts_time"]
            frame_time_ms = math.trunc(float(frame_time_s) * 1000.0)
            frame_size = frame["pkt_size"]
            transformed_data.append(
                f"{frame_number} {frame_type} {frame_time_ms} {frame_size}"
            )

        return '\n'.join(transformed_data)

    def _try_convert_data(self) -> str:
        """Attempts to convert ffprobe data.

        Returns an empty string on failure.
        """
        result: str
        try:
            result = self._convert_data()
        except ValueError as ex:
            log.error(
                "While converting data, the following exception was raised %s",
                ex)
            result = ""

        return result

    def _write_data_to_file(self, transformed_data: str) -> bool:
        """Attempts to write the transformed data to the output file."""
        try:
            with open(self._output_filename, 'x', encoding="utf-8")\
                    as output_file:
                output_file.write(transformed_data)
        except OSError:
            log.error("Could not open output file '%s', "
                      "ensure it does not exist already.",
                      self._output_filename)
            return False
        return True

    def run(self) -> bool:
        """Returns whether the transformation succeeded."""
        transformed_data = self._try_convert_data()
        if not transformed_data:
            return False

        return self._write_data_to_file(transformed_data)
