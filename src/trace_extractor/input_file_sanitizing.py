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
"""Sanitizes the input files to removed duplicates, invalid and non-mp4 files.
"""

import os

from .logger import log


class InputFilesSanitiser:
    """Sanitizer for input files.

    Given a list of files it checks:
    - if the file exists
    - if the file ends in mp4
    - if several files have the same basename
    - if the file appears several times
    In the latter two cases, only the first occurence is kept
    """

    def __init__(self, input_paths: list[str]) -> None:
        self._input_paths = input_paths
        self._existing_paths: list[str] = []
        self._existing_filenames: list[str] = []
        self._deduped_filenames: list[str] = []
        self._filtered_filenames: list[str] = []

    def _check_paths_existence(self) -> None:
        """Checks if each given path exists."""
        for path in self._input_paths:
            if os.path.exists(path):
                self._existing_paths.append(path)
            else:
                log.warning("The path '%s' does not exits. "
                            "It has been removed from the list.",
                            path)

    def _check_paths_are_files(self) -> None:
        """Checks if existing paths point to files."""
        for path in self._existing_paths:
            if os.path.isfile(path):
                self._existing_filenames.append(path)
            else:
                log.warning("The path '%s' does not point to a file. "
                            "It has been removed from the list.",
                            path)

    def _dedupe_filenames(self) -> None:
        """Removes all path that points to the same file."""
        chosen_basenames: dict[str, str] = {}
        chosen_realpaths: dict[str, str] = {}
        for filename in self._existing_filenames:

            basename = os.path.basename(filename)
            realpath = os.path.realpath(filename)

            if basename in chosen_basenames:
                log.warning("The files '%s' and '%s' have the same "
                            "basename, only the first will be kept.",
                            chosen_basenames[basename], filename)
            elif realpath in chosen_realpaths:
                log.warning("The files '%s' and '%s' are the same, "
                            "only the first will be kept.",
                            chosen_realpaths[realpath], filename)
            else:
                self._deduped_filenames.append(filename)
                chosen_basenames[basename] = filename
                chosen_realpaths[realpath] = filename

    def _filter_filenames(self) -> None:
        """Checks for the correct file extension."""
        for filename in self._deduped_filenames:
            if filename.lower().endswith(".mp4"):
                self._filtered_filenames.append(filename)
            else:
                log.warning("File '%s' does not end in '.mp4' "
                            "and will be ignored.", filename)

    def run(self) -> list[str]:
        """Returns the list of sanitized filenames."""
        self._check_paths_existence()
        self._check_paths_are_files()
        self._dedupe_filenames()
        self._filter_filenames()
        return self._filtered_filenames
