# basm

Basm is an assembler & debugger for one of [Mattbatwings'](https://www.youtube.com/@mattbatwings) Minecraft CPUs.

# Assembler

To compile an assembly program, use the following command:
```shell
python basm.py input.basm output.bin
```
If you want to assemble the program and generate debug information, use the -d flag as shown below:
```shell
python basm.py -d input.basm output.bin
```

# Debugger

To debug a program, use the following command:
```shell
python bdbg.py output.bin
```

The debugger has 4 windows:
- `source` - This window displays the source code (if present) of the program you're running.
- `registers & flags` - This window displays the values of the general purpose registers, the program counter and the flags.
- `memory` - This window displays the values in memory.
- `message` - This window displays any potential messages the emulator emits, such as when the program has halted, something went wrong, etc.

To control the debugger, use the following keys:
- `down` - Scrolls the source view down.
- `up` - Scrolls the source view up.
- `s` - Steps the emulator forward by one clock cycle.
- `r` - Restarts the program.
- `q` - Quits the debugger.

# Getting started

To learn Matt's assembly language I recommend you read [the ISA](https://docs.google.com/spreadsheets/d/1Bj3wHV-JifR2vP4HRYoCWrdXYp3sGMG0Q58Nm56W4aI). After that you can check out the examples in the examples folder and assemble them, step through them with the bdbg, modify them, etc.
