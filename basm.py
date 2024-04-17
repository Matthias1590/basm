import json
import sys

labels = {}

def get_current_address() -> int:
    return len(machine_code) // 2

def assemble(opcode: str, args: list[str]) -> int:
    if opcode == "ldi":
        assert_amount_of_args(args, 2)
        return 0b1010 << 12 | assemble_reg(args[0]) << 9 | assemble_immediate(args[1])
    elif opcode == "jmp":
        assert_amount_of_args(args, 1)
        return 0b0010 << 12 | assemble_address(args[0])
    elif opcode == "nop":
        assert_amount_of_args(args, 0)
        return 0b0000 << 12
    elif opcode == "hlt":
        assert_amount_of_args(args, 0)
        return 0b0001 << 12
    elif opcode == "brh":
        assert_amount_of_args(args, 2)
        return 0b0011 << 12 | assemble_condition(args[0]) << 10 | assemble_address(args[1])
    elif opcode == "cal":
        assert_amount_of_args(args, 1)
        return 0b0100 << 12 | assemble_address(args[0])
    elif opcode == "ret":
        assert_amount_of_args(args, 0)
        return 0b0101 << 12
    elif opcode == "pld":
        assert_amount_of_args(args, 2)
        return 0b0110 << 12 | assemble_reg(args[0]) << 9 | assemble_immediate(args[1], port=True)
    elif opcode == "pst":
        assert_amount_of_args(args, 2)
        return 0b0111 << 12 | assemble_reg(args[0]) << 9 | assemble_immediate(args[1], port=True)
    elif opcode == "mld":
        assert_amount_of_args(args, 3)
        return 0b1000 << 12 | assemble_reg(args[0]) << 9 | assemble_reg(args[1]) << 6 | assemble_offset(args[2])
    elif opcode == "mst":
        assert_amount_of_args(args, 3)
        return 0b1001 << 12 | assemble_reg(args[0]) << 9 | assemble_reg(args[1]) << 6 | assemble_offset(args[2])
    elif opcode == "adi":
        assert_amount_of_args(args, 2)
        return 0b1011 << 12 | assemble_reg(args[0]) << 9 | assemble_immediate(args[1])
    elif opcode == "add":
        assert_amount_of_args(args, 3)
        return 0b1100 << 12 | assemble_reg(args[0]) << 9 | assemble_reg(args[1]) << 6 | assemble_reg(args[2])
    elif opcode == "sub":
        assert_amount_of_args(args, 3)
        return 0b1101 << 12 | assemble_reg(args[0]) << 9 | assemble_reg(args[1]) << 6 | assemble_reg(args[2])
    elif opcode == "bit":
        assert_amount_of_args(args, 4)
        return 0b1110 << 12 | assemble_reg(args[0]) << 9 | assemble_reg(args[1]) << 6 | assemble_operation(args[2]) << 3 | assemble_reg(args[3])
    elif opcode == "rsh":
        assert_amount_of_args(args, 2)
        return 0b1111 << 12 | assemble_reg(args[0]) << 9 | assemble_reg(args[1]) << 6
    # psuedo-instructions
    elif opcode == "cmp":
        assert_amount_of_args(args, 2)
        return assemble("sub", ["r0", *args])
    elif opcode == "mov":
        assert_amount_of_args(args, 2)
        return assemble("add", [*args, "r0"])
    elif opcode == "lsh":
        assert_amount_of_args(args, 2)
        return assemble("add", [*args, args[1]])
    elif opcode == "inc":
        assert_amount_of_args(args, 1)
        return assemble("adi", [*args, "1"])
    elif opcode == "dec":
        assert_amount_of_args(args, 1)
        return assemble("adi", [*args, "-1"])
    elif opcode == "orr":
        assert_amount_of_args(args, 3)
        return assemble("bit", [args[0], args[1], "or", args[2]])
    elif opcode == "and":
        assert_amount_of_args(args, 3)
        return assemble("bit", [args[0], args[1], "and", args[2]])
    elif opcode == "xor":
        assert_amount_of_args(args, 3)
        return assemble("bit", [args[0], args[1], "xor", args[2]])
    elif opcode == "imp":
        assert_amount_of_args(args, 3)
        return assemble("bit", [args[0], args[1], "implies", args[2]])
    elif opcode == "nor":
        assert_amount_of_args(args, 3)
        return assemble("bit", [args[0], args[1], "nor", args[2]])
    elif opcode == "nnd":
        assert_amount_of_args(args, 3)
        return assemble("bit", [args[0], args[1], "nand", args[2]])
    elif opcode == "xnr":
        assert_amount_of_args(args, 3)
        return assemble("bit", [args[0], args[1], "xnor", args[2]])
    elif opcode == "nmp":
        assert_amount_of_args(args, 3)
        return assemble("bit", [args[0], args[1], "nimplies", args[2]])
    elif opcode == "not":
        assert_amount_of_args(args, 2)
        return assemble("bit", [args[0], args[1], "nor", "r0"])
    else:
        print(f"{input_path}:{line_number}: unknown opcode {opcode!r}")
        exit(1)

def assert_amount_of_args(args: list[str], amount: int) -> None:
    if len(args) != amount:
        print(f"{input_path}:{line_number}: expected {amount} argument(s), got {len(args)}")
        exit(1)

def assemble_operation(op: str) -> int:
    if op == "or":
        return 0b000
    elif op == "and":
        return 0b001
    elif op == "xor":
        return 0b010
    elif op == "implies":
        return 0b011
    elif op == "nor":
        return 0b100
    elif op == "nand":
        return 0b101
    elif op == "xnor":
        return 0b110
    elif op == "nimplies":
        return 0b111
    else:
        print(f"{input_path}:{line_number}: unknown operation {op!r}")
        exit(1)

def assemble_condition(cond: str) -> int:
    if cond == "eq":
        return 0b00
    elif cond == "ne":
        return 0b01
    elif cond == "ge":
        return 0b10
    elif cond == "lt":
        return 0b11
    else:
        print(f"{input_path}:{line_number}: unknown condition {cond!r}")
        exit(1)

def assemble_offset(offset: str) -> int:
    try:
        base = 10
        if "0x" in offset:
            base = 16
            offset = offset.replace("0x", "")
        elif "0b" in offset:
            base = 2
            offset = offset.replace("0b", "")

        offset_int = int(offset, base=base)
    except ValueError:
        print(f"{input_path}:{line_number}: expected offset, got {offset!r}")
        exit(1)

    if offset_int < -32 or offset_int > 31:
        print(f"{input_path}:{line_number}: offset must be between -32 and 31")
        exit(1)

    return offset_int & 0x3f

def assemble_address(addr: str) -> int:
    try:
        base = 10
        if "0x" in addr:
            base = 16
            addr = addr.replace("0x", "")
        elif "0b" in addr:
            base = 2
            addr = addr.replace("0b", "")

        addr_int = int(addr, base=base)
    except ValueError:
        if addr not in labels:
            print(f"{input_path}:{line_number}: unknown label or invalid integer address {addr!r}")
            exit(1)
        addr_int = labels[addr]

    if addr_int < 0 or addr_int >= 2**10:
        print(f"{input_path}:{line_number}: address must be between 0 and 1023")
        exit(1)

    return addr_int

def assemble_immediate(imm: str, port: bool = False) -> int:
    expected = "immediate"
    if port:
        expected = "port"

    try:
        base = 10
        if "0x" in imm:
            base = 16
            imm = imm.replace("0x", "")
        elif "0b" in imm:
            base = 2
            imm = imm.replace("0b", "")

        imm_int = int(imm, base=base)
    except ValueError:
        print(f"{input_path}:{line_number}: expected {expected}, got {imm!r}")
        exit(1)

    if imm_int < -128 or imm_int > 255:
        print(f"{input_path}:{line_number}: {expected} must be between -128 and 255")
        exit(1)

    return imm_int & 0xff

def assemble_reg(reg: str) -> int:
    if reg[0] != "r" or not reg[1:].isdigit():
        print(f"{input_path}:{line_number}: expected register, got {reg!r}")
        exit(1)

    reg_num = int(reg[1:])

    if reg_num >= 8:
        print(f"{input_path}:{line_number}: register number must be less than 8")
        exit(1)

    return reg_num

def assemble_file(_input_path: str, _output_path: str, debug: bool) -> None:
    global line_number
    global machine_code
    global input_path
    global output_path

    input_path = _input_path
    output_path = _output_path

    with open(input_path, "r") as f:
        source = f.read()

    debug_info = {
        "labels": {},
        "instructions": []
    }

    machine_code = b""

    # first pass: process labels
    line_number = 0
    for line in source.splitlines():
        line_number += 1

        # remove comment
        line = line.split("#")[0].strip()

        # process labels
        while ":" in line:
            label = line.split(":")[0].strip()
            line = ":".join(line.split(":")[1:]).strip()

            if label in labels:
                print(f"{input_path}:{line_number}: label {label!r} already defined")
                exit(1)
            labels[label] = get_current_address()

            debug_info["labels"][label] = {
                "line": line_number,
                "address": get_current_address()
            }

        # ignore empty lines
        if not line.strip():
            continue

        machine_code += b"\x00\x00"

    machine_code = b""

    # second pass: assemble instructions
    line_number = 0
    for line in source.splitlines():
        line_number += 1

        if get_current_address() >= 2**10:
            print(f"{input_path}:{line_number}: program too long")
            exit(1)

        # remove comment
        line = line.split("#")[0].strip()

        # remove labels
        while ":" in line:
            line = ":".join(line.split(":")[1:]).strip()

        # ignore empty lines
        if not line.strip():
            continue

        opcode, *args = line.split(maxsplit=1)
        if args:
            args = [arg.strip() for arg in args[0].split(",")]
        else:
            args = []
        if any([" " in arg for arg in args]):
            print(f"{input_path}:{line_number}: missing comma between arguments")
            exit(1)

        debug_info["instructions"].append({
            "line": line_number,
            "address": get_current_address(),
        })

        machine_code += assemble(opcode, args).to_bytes(2, "big")

    if debug:
        debug_info["source"] = source
        debug_info["source_path"] = input_path

        with open(f"{output_path}.dbg", "w") as f:
            json.dump(debug_info, f, indent=4)

    with open(output_path, "wb") as f:
        f.write(machine_code)

def print_help(error: bool) -> None:
    print(f"usage: {sys.argv[0]} [flags] <input.basm> <output.bin>")
    print("flags:")
    print("  -h, --help: show this help message")
    print("  -d, --debug: generate debug information (for use with bdbg)")

    exit(1 if error else 0)

if __name__ == "__main__":
    debug = False
    while len(sys.argv) > 1 and sys.argv[1].startswith("-"):
        if sys.argv[1] in ["-h", "--help"]:
            print_help(error=False)
        elif sys.argv[1] in ["-d", "--debug"]:
            debug = True
        else:
            print(f"unknown flag {sys.argv[1]!r}")
            print_help(error=True)

        sys.argv.pop(1)

    if len(sys.argv) < 3:
        print_help(error=True)

    assemble_file(sys.argv[1], sys.argv[2], debug)
