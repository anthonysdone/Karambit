VAR_BASE  = 0x0100  # Variables stored here
CODE_BASE = 0x0200  # Code starts here
STR_BASE  = 0x3000  # Strings stored here

OPCODES = {
    "LDI": 0x10,    # Load immediate    (LDI r, imm)
    "LDM": 0x11,    # Load memory       (LDM r, addr)
    "STM": 0x12,    # Store memory      (STM r, addr)
    "MOV": 0x13,    # Move register     (MOV rd, rs)

    "ADD": 0x20,    # Add registers     (ADD rd, rs)
    "ADDI": 0x21,   # Add immediate     (ADDI r, imm)
    "SUB": 0x22,    # Sub registers     (SUB rd, rs)
    "SUBI": 0x23,   # Sub immediate     (SUBI r, imm)

    "CMP": 0x30,    # Compare registers (CMP rd, rs)
    "JMP": 0x31,    # Jump always       (JMP addr)
    "JZ":  0x32,    # Jump if zero      (JZ addr)
    "JNZ": 0x33,    # Jump if not zero  (JNZ addr)
    "CMPI": 0x34,   # Compare immediate (CMPI r, imm)

    "SYS": 0x40,    # System call       (SYS imm)
    "HLT": 0x41     # Halt execution    (HLT)
}

SIZES = {
    0x10: 3,        # LDI
    0x11: 4,        # LDM
    0x12: 4,        # STM
    0x13: 3,        # MOV
    0x20: 3,        # ADD
    0x21: 3,        # ADDI
    0x22: 3,        # SUB
    0x23: 3,        # SUBI
    0x30: 3,        # CMP
    0x31: 3,        # JMP
    0x32: 3,        # JZ
    0x33: 3,        # JNZ
    0x34: 3,        # CMPI
    0x40: 2,        # SYS
    0x41: 1         # HLT
}

REGISTERS = {
    "R0": 0,
    "R1": 1,
    "R2": 2,
    "R3": 3,
}

def var_addr(var_char):
    return VAR_BASE + (ord(var_char.upper()) - ord("A"))