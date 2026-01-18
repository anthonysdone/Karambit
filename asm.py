from isa import *

def tokenize(line):
    line = line.replace(",", " ")
    return line.split()

def parse_number(s):
    s = s.strip()
    if s.startswith("0x") or s.startswith("0X"): 
        return int(s, 16)
    return int(s)

def extract_string(line):
    start = line.index('"') + 1
    end = line.rindex('"')
    return line[start:end]

def encode_string(s):
    result = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            if s[i + 1] == "n":
                result.append(10)
                i += 2
            elif s[i + 1] == '"':
                result.append(ord('"'))
                i += 2
            elif s[i + 1] == "\\":
                result.append(ord("\\"))
                i += 2
            else:
                raise ValueError(f"Unknown escape sequence: \\{s[i + 1]}")
        else:
            result.append(ord(s[i]))
            i += 1
    result.append(0)  # Null terminator
    return result

def resolve_address(operand, labels):
    if operand in labels: 
        return labels[operand]
    return parse_number(operand)
            
def encode_instruction(tokens, labels):
    mnemonic = tokens[0]
    opcode = OPCODES[mnemonic]

    if mnemonic == "HLT":
        return [opcode]

    elif mnemonic == "SYS":
        imm = parse_number(tokens[1])
        return [opcode, imm]
    
    if mnemonic in ["JMP", "JZ", "JNZ"]: 
        addr = resolve_address(tokens[1], labels)
        return [opcode, addr & 0xFF, (addr >> 8) & 0xFF]
    
    if mnemonic in ["LDI", "ADDI", "SUBI", "CMPI"]:
        r = REGISTERS[tokens[1].upper()]
        imm = parse_number(tokens[2])
        return [opcode, r, imm]
    
    if mnemonic in ["LDM", "STM"]:
        r = REGISTERS[tokens[1]]
        addr = resolve_address(tokens[2], labels)
        return [opcode, r, addr & 0xFF, (addr >> 8) & 0xFF]
    
    if mnemonic in ["MOV", "ADD", "SUB", "CMP"]:
        rd = REGISTERS[tokens[1]]
        rs = REGISTERS[tokens[2]]
        return [opcode, rd, rs]

def assemble(text): 
    lines = [line.split(";")[0].strip() for line in text.splitlines()]
    lines = [line for line in lines if line]

    labels = {}
    addr = CODE_BASE
    origin = CODE_BASE

    for line in lines:
        if line.startswith(".org"): 
            parts = line.split()
            addr = parse_number(parts[1])
            if origin == CODE_BASE: 
                origin = addr
            continue

        if ":" in line: 
            label_part, rest = line.split(":", 1)
            label = label_part.strip()
            labels[label] = addr
            line = rest.strip()
            if not line: 
                continue

        if line.startswith(".byte"):
            addr += 1
        elif line.startswith(".word"):
            addr += 2
        elif line.startswith(".string") or line.startswith(".asciiz"):
            text_content = extract_string(line)
            addr += len(encode_string(text_content))
        elif line:
            tokens = tokenize(line)
            if tokens[0] in OPCODES:
                size = SIZES[OPCODES[tokens[0]]]
                addr += size

    code = {}
    addr = CODE_BASE

    for line in lines: 
        if line.startswith(".org"):
            parts = line.split()
            addr = parse_number(parts[1])
            continue

        if ":" in line: 
            _, rest = line.split(":", 1)
            line = rest.strip()
            if not line: 
                continue


        if line.startswith(".byte"):
            val = parse_number(line.split()[1])
            code[addr] = val
            addr += 1

        elif line.startswith(".word"):
            val = parse_number(line.split()[1])
            code[addr] = val & 0xFF
            code[addr + 1] = (val >> 8) & 0xFF
            addr += 2

        elif line.startswith(".string") or line.startswith(".asciiz"):
            text_content = extract_string(line)
            for byte_val in encode_string(text_content):
                code[addr] = byte_val
                addr += 1

        elif line: 
            tokens = tokenize(line)
            if tokens[0] in OPCODES: 
                instruction_bytes = encode_instruction(tokens, labels)
                for byte_val in instruction_bytes:
                    code[addr] = byte_val
                    addr += 1
        
    if not code: 
        return (origin, bytes(), origin)
    
    min_addr = min(code.keys())
    max_addr = max(code.keys())
    blob = bytearray(max_addr - min_addr + 1)

    for addr, val in code.items():
        blob[addr - min_addr] = val

    entrypoint = labels.get("start", labels.get("_start", origin))
    return (min_addr, bytes(blob), entrypoint)
