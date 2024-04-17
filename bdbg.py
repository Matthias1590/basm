import curses
import curses.textpad
import json
import sys
import os

def print_help(error: bool) -> None:
    print(f"usage: {sys.argv[0]} [flags] <program.bin>")
    print("flags:")
    print("  -h, --help: show this help message")

    exit(1 if error else 0)

def debug_program(path: str) -> None:
    with open(path, "rb") as f:
        machine_code = f.read()

    if not os.path.exists(f"{path}.dbg"):
        print("debug information not found, run the assembler with the -d flag to generate debug information")
        exit(1)

    with open(f"{path}.dbg", "r") as f:
        debug_info = json.load(f)

    curses.wrapper(lambda stdscr: debug_loop(stdscr, machine_code, debug_info))

class Emulator:
    def __init__(self, machine_code: bytes) -> None:
        self.machine_code = machine_code
        self.pc = 0
        self.memory = [0] * 256
        self.regs = [ZeroRegister(), *[Register() for _ in range(7)]]
        self.zero = False
        self.carry = False
        self.stack = []

    def step(self) -> str:
        return self.execute_instruction(int.from_bytes(self.machine_code[self.pc * 2:self.pc * 2 + 2], "big"))

    def execute_instruction(self, instruction: int) -> str | None:
        opcode = instruction >> 12
        arg_reg_a = (instruction >> 9) & 0b111
        arg_reg_b = (instruction >> 6) & 0b111
        arg_reg_c = instruction & 0b111
        arg_address = instruction & 0x3ff
        arg_condition = (instruction >> 10) & 0b11
        arg_operation = (instruction >> 3) & 0b111
        arg_offset = instruction & 0x3f
        arg_immediate = instruction & 0xff

        if opcode == 0b1010:  # ldi
            self.regs[arg_reg_a].write(arg_immediate)
        elif opcode == 0b1101:  # sub
            self.zero, self.carry = self.regs[arg_reg_a].write(self.regs[arg_reg_b].get() - self.regs[arg_reg_c].get())
        elif opcode == 0b0011:  # brh
            if ((arg_condition == 0b00 and self.zero)
                or (arg_condition == 0b01 and not self.zero)
                or (arg_condition == 0b10 and self.carry)
                or (arg_condition == 0b11 and not self.carry)):
                self.pc = arg_address - 1
        elif opcode == 0b0000:  # nop
            pass
        elif opcode == 0b0001:  # hlt
            return "halted"
        elif opcode == 0b0010:  # jmp
            self.pc = arg_address - 1
        elif opcode == 0b0100:  # cal
            self.stack.append(self.pc)
            self.pc = arg_address - 1
        elif opcode == 0b0101:  # ret
            self.pc = self.stack.pop()
        elif opcode == 0b0110:  # pld
            return "port io is not implemented yet"
        elif opcode == 0b0111:  # pst
            return "port io is not implemented yet"
        elif opcode == 0b1000:  # mld
            self.regs[arg_reg_a].write(self.memory[self.regs[arg_reg_b].get() + arg_offset])
        elif opcode == 0b1001:  # mst
            self.memory[self.regs[arg_reg_b].get() + arg_offset] = self.regs[arg_reg_a].get()
        elif opcode == 0b1011:  # adi
            self.zero, self.carry = self.regs[arg_reg_a].write(self.regs[arg_reg_a].get() + arg_immediate)
        elif opcode == 0b1100:  # add
            self.zero, self.carry = self.regs[arg_reg_a].write(self.regs[arg_reg_b].get() + self.regs[arg_reg_c].get())
        elif opcode == 0b1110:  # bit
            if arg_operation == 0b000:  # or
                self.zero, self.carry = self.regs[arg_reg_a].write(self.regs[arg_reg_b].get() | self.regs[arg_reg_c].get())
            elif arg_operation == 0b001:  # and
                self.zero, self.carry = self.regs[arg_reg_a].write(self.regs[arg_reg_b].get() & self.regs[arg_reg_c].get())
            elif arg_operation == 0b010:  # xor
                self.zero, self.carry = self.regs[arg_reg_a].write(self.regs[arg_reg_b].get() ^ self.regs[arg_reg_c].get())
            elif arg_operation == 0b011:  # implies
                self.zero, self.carry = self.regs[arg_reg_a].write((~self.regs[arg_reg_b].get()) | self.regs[arg_reg_c].get())
            elif arg_operation == 0b100:  # nor
                self.zero, self.carry = self.regs[arg_reg_a].write(~(self.regs[arg_reg_b].get() | self.regs[arg_reg_c].get()))
            elif arg_operation == 0b101:  # nand
                self.zero, self.carry = self.regs[arg_reg_a].write(~(self.regs[arg_reg_b].get() & self.regs[arg_reg_c].get()))
            elif arg_operation == 0b110:  # xnor
                self.zero, self.carry = self.regs[arg_reg_a].write(~(self.regs[arg_reg_b].get() ^ self.regs[arg_reg_c].get()))
            elif arg_operation == 0b111:  # nimplies
                self.zero, self.carry = self.regs[arg_reg_a].write(self.regs[arg_reg_b].get() & (~self.regs[arg_reg_c].get()))
        elif opcode == 0b1111:  # rsh
            self.regs[arg_reg_a].write(self.regs[arg_reg_b].get() >> 1 if self.regs[arg_reg_b].get() >= 0 else (self.regs[arg_reg_b].get() + 2**8) >> 1)
        else:
            return f"unknown opcode {bin(opcode)} at address {hex(self.pc)}"

        self.pc += 1
        return None

class Register:
    def __init__(self) -> None:
        self.value = 0

    def write(self, value: int) -> tuple[bool, bool]:
        self.value = value & 0xff
        return self.value == 0, self.value < 0

    def get(self) -> int:
        return self.value

class ZeroRegister(Register):
    def get(self) -> int:
        return 0

def get_line_number(debug_info: dict, pc: int) -> int:
    for instruction in debug_info["instructions"]:
        if instruction["address"] == pc:
            return instruction["line"]

    return None

def debug_loop(stdscr, machine_code: bytes, debug_info: dict) -> None:
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)

    stdscr.clear()
    stdscr.nodelay(1)

    REGISTERS_WINDOW_WIDTH = 53

    emulator = Emulator(machine_code)

    scroll = 0
    message = None

    while True:
        stdscr.erase()

        height, width = stdscr.getmaxyx()

        source_win = stdscr.derwin(height - 2, width - 1 - REGISTERS_WINDOW_WIDTH, 0, 0)

        source_win.addstr(0, 1, f"  source ({debug_info['source_path']})".ljust(source_win.getmaxyx()[1] - 1), curses.color_pair(1))
        for y in range(height - 3):
            line_number = y + scroll + 1

            line = ""
            if line_number - 1 < len(debug_info["source"].split("\n")):
                line = debug_info["source"].split("\n")[line_number - 1]

            color = curses.color_pair(2)
            if get_line_number(debug_info, emulator.pc) == line_number:
                color = curses.color_pair(1)

            source_win.addstr(y + 1, 1, f" {str(line_number).rjust(4)} ", color)

            if len(line) > source_win.getmaxyx()[1] - 9:
                line = line[:source_win.getmaxyx()[1] - 13] + "..."
            source_win.addstr(y + 1, 7, f" | {line}")

        source_win.refresh()

        message_win = stdscr.derwin(2, width - 1 - REGISTERS_WINDOW_WIDTH, height - 2, 0)

        message_win.addstr(0, 1, "  message".ljust(message_win.getmaxyx()[1] - 1), curses.color_pair(1))
        if message:
            display_message = f"  {message}"
            if len(display_message) >= message_win.getmaxyx()[1]:
                display_message = display_message[:message_win.getmaxyx()[1] - 4] + "..."

            message_win.addstr(1, 0, display_message)

        message_win.refresh()

        memory_win = stdscr.derwin(height - 6, REGISTERS_WINDOW_WIDTH, 6, width - 1 - REGISTERS_WINDOW_WIDTH)

        memory_win.addstr(0, 1, "  memory".ljust(memory_win.getmaxyx()[1] - 1), curses.color_pair(1))
        for i in range(0x10):
            memory_win.addstr(1, 4 + i * 3, f" {i:02X}", curses.color_pair(2))
        for y in range(min(height - 8, 0x10)):
            memory_win.addstr(y + 2, 1, f" {y * 16:02X}", curses.color_pair(2))

            for x in range(0x10):
                value = emulator.memory[y * 0x10 + x]
                memory_win.addstr(y + 2, 4 + x * 3, f" {value:02X}")

        memory_win.refresh()

        registers_win = stdscr.derwin(height - 2, REGISTERS_WINDOW_WIDTH, 0, width - 1 - REGISTERS_WINDOW_WIDTH)

        registers_win.addstr(0, 1, "  registers & flags".ljust(registers_win.getmaxyx()[1] - 1), curses.color_pair(1))
        for i in range(2):
            offset = 1
            for j in range(4):
                index = i * 4 + j
                value = emulator.regs[index].get()

                registers_win.addstr(i + 1, offset, f" r{index}", curses.color_pair(2))
                registers_win.addstr(i + 1, offset + 3, f": {str(value).rjust(4)}")

                offset += 13
        registers_win.addstr(4, 1, f" zero", curses.color_pair(2))
        registers_win.addstr(4, 6, f":  {int(emulator.zero)}")
        registers_win.addstr(4, 14, f" carry", curses.color_pair(2))
        registers_win.addstr(4, 20, f": {int(emulator.carry)}")
        registers_win.addstr(4, 27, f" pc", curses.color_pair(2))
        registers_win.addstr(4, 30, f":  {emulator.pc:03X}")

        registers_win.refresh()

        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_DOWN and scroll < debug_info["source"].count("\n"):
            scroll += 1
        elif key == curses.KEY_UP and scroll > 0:
            scroll -= 1
        elif key == ord("s"):
            message = emulator.step()

            if get_line_number(debug_info, emulator.pc) - scroll > height - 3 or get_line_number(debug_info, emulator.pc) < scroll + 1:
                scroll = get_line_number(debug_info, emulator.pc) - 1
        elif key == ord("q"):
            break
        elif key == ord("r"):
            emulator = Emulator(machine_code)
            message = None
            scroll = 0

if __name__ == "__main__":
    while len(sys.argv) > 1 and sys.argv[1].startswith("-"):
        if sys.argv[1] in ["-h", "--help"]:
            print_help(error=False)
        else:
            print(f"unknown flag {sys.argv[1]!r}")
            print_help(error=True)

        sys.argv.pop(1)

    if len(sys.argv) < 2:
        print_help(error=True)

    debug_program(sys.argv[1])
