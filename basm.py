labels = {}

def get_current_address() -> int:
    return len(machine_code) // 2

def assemble(opcode: str, args: list[str]) -> int:
    if opcode == "ldi":
        return 0b1010 << 12 | assemble_reg(args[0]) << 9 | assemble_immediate(args[1])
    elif opcode == "jmp":
        return 0b0010 << 12 | assemble_address(args[0])
    elif opcode == "nop":
        return 0b0000 << 12
    elif opcode == "hlt":
        return 0b0001 << 12
    elif opcode == "brh":
        return 0b0011 << 12 | assemble_condition(args[0]) << 10 | assemble_address(args[1])
    elif opcode == "cal":
        return 0b0100 << 12 | assemble_address(args[0])
    elif opcode == "ret":
        return 0b0101 << 12
    elif opcode == "pld":
        return 0b0110 << 12 | assemble_reg(args[0]) << 9 | assemble_immediate(args[1], port=True)
    elif opcode == "pst":
        return 0b0111 << 12 | assemble_reg(args[0]) << 9 | assemble_immediate(args[1], port=True)
    elif opcode == "mld":
        return 0b1000 << 12 | assemble_reg(args[0]) << 9 | assemble_reg(args[1]) << 6 | assemble_offset(args[2])
    elif opcode == "mst":
        return 0b1001 << 12 | assemble_reg(args[0]) << 9 | assemble_reg(args[1]) << 6 | assemble_offset(args[2])
    elif opcode == "adi":
        return 0b1011 << 12 | assemble_reg(args[0]) << 9 | assemble_immediate(args[1])
    elif opcode == "add":
        return 0b1100 << 12 | assemble_reg(args[0]) << 9 | assemble_reg(args[1]) << 6 | assemble_reg(args[2])
    elif opcode == "sub":
        return 0b1101 << 12 | assemble_reg(args[0]) << 9 | assemble_reg(args[1]) << 6 | assemble_reg(args[2])
    elif opcode == "bit":
        return 0b1110 << 12 | assemble_reg(args[0]) << 9 | assemble_reg(args[1]) << 6 | assemble_operation(args[2]) << 3 | assemble_reg(args[3])
    elif opcode == "rsh":
        return 0b1111 << 12 | assemble_reg(args[0]) << 9 | assemble_reg(args[1]) << 6
    # psuedo-instructions
    elif opcode == "cmp":
        return assemble("sub", ["r0", *args])
    elif opcode == "mov":
        return assemble("add", [*args, "r0"])
    elif opcode == "lsh":
        return assemble("add", [*args, args[1]])
    elif opcode == "inc":
        return assemble("adi", [*args, "1"])
    elif opcode == "dec":
        return assemble("adi", [*args, "-1"])
    elif opcode == "orr":
        return assemble("bit", [args[0], args[1], "or", args[2]])
    elif opcode == "and":
        return assemble("bit", [args[0], args[1], "and", args[2]])
    elif opcode == "xor":
        return assemble("bit", [args[0], args[1], "xor", args[2]])
    elif opcode == "imp":
        return assemble("bit", [args[0], args[1], "implies", args[2]])
    elif opcode == "nor":
        return assemble("bit", [args[0], args[1], "nor", args[2]])
    elif opcode == "nnd":
        return assemble("bit", [args[0], args[1], "nand", args[2]])
    elif opcode == "xnr":
        return assemble("bit", [args[0], args[1], "xnor", args[2]])
    elif opcode == "nmp":
        return assemble("bit", [args[0], args[1], "nimplies", args[2]])
    elif opcode == "not":
        return assemble("bit", [args[0], args[1], "nor", "r0"])
    else:
        print(f"{input_path}:{line_number}: unknown opcode {opcode!r}")
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

def assemble_file(_input_path: str, _output_path: str) -> None:
    global line_number
    global machine_code
    global input_path
    global output_path

    input_path = _input_path
    output_path = _output_path

    with open(input_path, "r") as f:
        source = f.read()

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
        args = args[0] if args else ""
        args = [arg.strip() for arg in args.split(",")]
        if any([" " in arg for arg in args]):
            print(f"{input_path}:{line_number}: missing comma between arguments")
            exit(1)

        machine_code += assemble(opcode, args).to_bytes(2, "big")

    with open(output_path, "wb") as f:
        f.write(machine_code)

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} input.asm output.bin")
        exit(1)
    
    assemble_file(sys.argv[1], sys.argv[2])
