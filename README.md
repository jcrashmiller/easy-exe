# Easy EXE

Automatic Windows executable launcher for Linux.

Easy EXE reduces friction for users encountering Windows software on Linux by automatically detecting the type of executable and selecting an appropriate runtime (Wine or DOSBox), along with sensible default configurations.

This project focuses on making legacy and Windows-only software easier to *try* and *understand* on Linux — without requiring deep knowledge of emulation tools.

## Status

**In Development — Not Ready for Use**

This project is under active design and experimentation.
Installation and use are not yet recommended.

## How it works (high level)

1. A `.exe` file is invoked directly or via double-click
2. Easy EXE inspects the executable to determine:
   - DOS vs Windows
   - Application vs game
3. A suitable runtime (Wine or DOSBox) is selected
4. A configuration is generated using known heuristics and program-specific rules
5. The executable is launched in an isolated, transparent environment

## Features

- Automatic detection of DOS vs Windows executables
- Game vs application–aware runtime configuration
- Program-specific heuristics for well-known software
- Transparent Wine prefix management
- Automatic DOSBox configuration generation
- Cross-distribution compatibility

## Supported Software (Examples)

**DOS Games**
- DOOM
- Duke Nukem 3D
- Prince of Persia
- SimCity 2000

**DOS Applications**
- Turbo Pascal
- Norton Commander
- Lotus 1-2-3

**Windows Applications**
- WinRAR
- Microsoft Money

**Windows Games**
- Black & White 2
- Pong: The Next Level

> Support is rule-based and heuristic-driven; not all programs are guaranteed to work.

## Quick Start (Development Only)

1. Install dependencies:
   ```
   ./scripts/install_dependencies.sh
   ```
2. Run Easy EXE:
   ``` 
   python3 easy_exe.py /path/to/program.exe
   ```
3. (Optional) Register Easy EXE as a default handler:
   ``` 
   python3 scripts/register_handler.py
   ``` 

## Roadmap

- Safer default configurations
- Improved program fingerprinting
- Dry-run / inspection mode
- Better visibility into generated runtime settings
