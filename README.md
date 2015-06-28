Miscellaneous scripts
=====================

These scripts are made for personal use, so may not be high quality code.

- debworld.py

Mantain deb packages in a Gentoo's world file way. Define packages which should be installed and its mode (automatic or manual). Packages not listed (and not being essential, or having a low priority) are marked automatic if not explicitly present on packages files definitions.

Essential packages and packages with priority lower to three are always installed and marked manual.
