[license-url]: https://github.com/revisto/drum-machine/blob/master/COPYING
[license-image]: https://img.shields.io/github/license/revisto/drum-machine.svg?style=for-the-badge
[flathub-url]: https://flathub.org/apps/io.github.revisto.drum-machine
[flathub-image]: https://img.shields.io/flathub/v/io.github.revisto.drum-machine?logo=flathub&style=for-the-badge
[issues-url]: https://github.com/revisto/drum-machine/issues
[issues-image]: https://img.shields.io/github/issues/revisto/drum-machine?style=for-the-badge

<div align="center">
  <img src="data/icons/hicolor/scalable/apps/io.github.revisto.drum-machine.svg" width="128" height="128">

  # Drum Machine

  **Create and play drum beats**

  [![License][license-image]][license-url]
  [![Flathub][flathub-image]][flathub-url]
  [![Issues][issues-image]][issues-url]

  <img src="data/screenshots/pattern-dark.png">
</div>

## Description
Drum Machine is a modern and intuitive application for creating, playing, and managing drum patterns. Perfect for musicians, producers, and anyone interested in rhythm creation, this application provides a simple interface for drum pattern programming.

## Features
- Intuitive grid-based pattern editor
- Adjustable BPM control
- Volume control for overall mix
- Save and load preset patterns 
- Multiple drum sounds including kick, snare, hi-hat, and more
- Keyboard shortcuts for quick access to all functions
- Modern GTK4 and libadwaita interface

## Install

<a href="https://flathub.org/apps/details/io.github.revisto.drum-machine">
<img width="200" alt="Download on Flathub" src="https://flathub.org/api/badge?svg&locale=en"/>
</a>

### Build from source

You can clone and run from GNOME Builder.

#### Requirements

- Python 3 `python`
- PyGObject `python-gobject`
- GTK4 `gtk4`
- libadwaita `libadwaita`
- pygame `pygame`
- mido `mido` 
- Meson `meson`
- Ninja `ninja`

Run these commands to build it with meson:
```bash
meson builddir --prefix=/usr/local
sudo ninja -C builddir install
```

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Play/Pause | Space |
| Clear All | Ctrl+Delete |
| Increase BPM | Plus/Equal |
| Decrease BPM | Minus |
| Increase Volume | Ctrl+Up |
| Decrease Volume | Ctrl+Down |
| Load Preset | Ctrl+O |
| Save Preset | Ctrl+S |
| Quit | Ctrl+Q |

## Credits
Developed by **[Revisto](https://github.com/revisto)**.

## License
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.