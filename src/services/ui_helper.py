# services/ui_helper.py
#
# Copyright 2024 revisto
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later


class UIHelper:
    def __init__(self, window, toggle_parts, num_toggles):
        self.window = window
        self.toggle_parts = toggle_parts
        self.num_toggles = num_toggles

    def update_toggle_ui(self, index, add_class=True):
        for part in self.toggle_parts:
            toggle = getattr(self.window, f"{part}_toggle_{index + 1}")
            if add_class:
                toggle.get_style_context().add_class("toggle-active")
            else:
                toggle.get_style_context().remove_class("toggle-active")

    def highlight_playing_bar(self, index):
        for i in range(self.num_toggles):
            self.update_toggle_ui(i, add_class=False)
        self.update_toggle_ui(index, add_class=True)

    def clear_highlight(self):
        for i in range(self.num_toggles):
            self.update_toggle_ui(i, add_class=False)

    def clear_all_toggles(self):
        for part in self.toggle_parts:
            for i in range(self.num_toggles):
                toggle = getattr(self.window, f"{part}_toggle_{i + 1}")
                toggle.set_active(False)
