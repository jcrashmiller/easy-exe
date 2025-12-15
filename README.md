# Easy EXE

Automatic Windows executable launcher for Linux. Double-click any .exe file and Easy EXE will automatically detect and configure the best tool (Wine/DOSBox) with optimal settings.

# **IN DEVELOPMENT - NOT READY FOR USE**
**Do Not Install**
**Do Not Use**

## Quick Start

1. Install dependencies: `./scripts/install_dependencies.sh`
2. Run: `python3 easy_exe.py /path/to/program.exe`
3. Register as default handler: `python3 scripts/register_handler.py`

## Features

- Automatic detection of DOS vs Windows programs
- Game vs application optimized settings
- Specific configurations for 100+ popular programs
- Transparent Wine prefix management
- DOSBox configuration generation
- Cross-distribution compatibility

## Supported Programs

- DOS Games: DOOM, Duke Nukem 3D, Prince of Persia, SimCity 2000, etc.
- DOS Applications: Turbo Pascal, Norton Commander, Lotus 1-2-3, etc.
- Windows Applications: WinRAR, Microsoft Money, etc.
- Windows Games: Black & White 2, Pong: The Next Level, etc.
