from isa import *
from asm import encode_string

def compile_expr(expr):
    expr = expr.strip()

    if expr.isdigit():
        return [f"  LDI R0, {expr}"]
    
    if len(expr) == 1 and expr.isalpha(): 
        return [f"  LDM R0, 0x{var_addr(expr):04X}"]
    
    for op in ["+", "-"]: 
        if op in expr: 
            parts = expr.split(op)
            left = parts[0].strip()
            right = parts[1].strip()

            if left.isalpha() and right.isdigit():
                code = [f"  LDM R0, 0x{var_addr(left):04X}"]
                if op == "+":
                    code.append(f"  ADDI R0, {right}")
                else:
                    code.append(f"  SUBI R0, {right}")
                return code

            if left.isalpha() and right.isalpha():
                code = [
                    f"  LDM R0, 0x{var_addr(left):04X}",
                    f"  LDM R1, 0x{var_addr(right):04X}"
                ]
                if op == "+":
                    code.append("  ADD R0, R1")
                else:
                    code.append("  SUB R0, R1")
                return code
    return [f"    LDI R0, 0"]

def compile_condition(cond): 
    cond = cond.strip()

    if "=" in cond and "<>" not in cond: 
        parts = cond.split("=")
        left = parts[0].strip()
        right = parts[1].strip()

        code = compile_expr(left)
        code.append("  MOV R3, R0")
        code.extend(compile_expr(right))
        code.append("  CMP R3, R0")
        return code
    
    if "<>" in cond: 
        parts = cond.split("<>")
        left = parts[0].strip()
        right = parts[1].strip()

        code = compile_expr(left)
        code.append("  MOV R3, R0")
        code.extend(compile_expr(right))
        code.append("  CMP R3, R0")
        return code

    return []

def compile_statement(stmt, strings): 
    tokens = stmt.split()
    if not tokens: 
        return []

    cmd = tokens[0].upper()

    # LET V = EXPR
    if cmd == "LET":
        var = tokens[1]
        expr = " ".join(tokens[3:])
        code = compile_expr(expr)
        code.append(f"  STM R0, 0x{var_addr(var):04X}")
        return code
    
    # PRINT "string"
    if cmd == "PRINT":
        text = stmt[stmt.index('"')+1:stmt.rindex('"')]
        strings.append(text)
        str_idx = len(strings) - 1
        addr = STR_BASE
        for s in strings[:str_idx]:
            addr += len(encode_string(s))
        return [
            f"  LDI R0, {addr & 0xFF}",
            f"  LDI R1, {(addr >> 8) & 0xFF}",
            "  SYS 1"
        ]
    
    # PRINTC EXPR
    if cmd == "PRINTC":
        expr = " ".join(tokens[1:])
        code = compile_expr(expr)
        code.append("  SYS 0")
        return code
    
    # CLS
    if cmd == "CLS": 
        return ["  SYS 2"]

    # PLOT X, Y, C
    if cmd == "PLOT":
        x_expr = tokens[1].rstrip(",")
        y_expr = tokens[2].rstrip(",")
        c_expr = tokens[3]
        code = compile_expr(x_expr)
        code.append("  MOV R3, R0")
        code.extend(compile_expr(y_expr))
        code.append("  MOV R1, R0")
        code.append("  MOV R0, R3")
        code.extend(compile_expr(c_expr))
        code.append("  MOV R2, R0")
        code.append("  SYS 3")
        return code
    
    # RENDER
    if cmd == "RENDER":
        return ["  SYS 4"]
    
    # SLEEP MS
    if cmd == "SLEEP":
        expr = " ".join(tokens[1:])
        code = compile_expr(expr)
        code.append("  SYS 5")
        return code
    
    # KEY V
    if cmd == "KEY":
        var = tokens[1]
        return [
            "  SYS 6",
            f"  STM R0, 0x{var_addr(var):04X}"
        ]
    
    # GOTO LABEL
    if cmd == "GOTO":
        label = tokens[1]
        return [f"  JMP {label}"]
    
    # IF COND THEN GOTO label
    if cmd == "IF":
        then_idx = stmt.upper().index("THEN")
        cond = stmt[3:then_idx].strip()
        goto_part = stmt[then_idx + 4:].strip()
        label = goto_part.split()[1]

        code = compile_condition(cond)
        if "<>" in cond:
            code.append(f"  JNZ {label}")
        else:
            code.append(f"  JZ {label}")
        return code
    
    if cmd == "END":
        return ["  HLT"]
    
    return []

def compile_basic(source):
    lines = [line.strip() for line in source.split("\n")]
    lines = [line for line in lines if line and not line.startswith("#")]

    statements = []
    for line in lines:
        label = None
        stmt = line

        if ":" in line: 
            parts = line.split(":", 1)
            label = parts[0].strip()
            stmt = parts[1].strip() if len(parts) > 1 else ""

        statements.append((label, stmt))
    
    asm = [".org 0x0200", "start:"]
    strings = []

    for label, stmt in statements:
        if label:
            asm.append(f"{label}:")
        if stmt:
            asm.extend(compile_statement(stmt, strings))

    asm.append("  HLT")
    asm.append("")

    if strings:
        asm.append(".org 0x3000")
        addr = STR_BASE
        for i, text in enumerate(strings):
            asm.append(f'str_{i}: .string "{text}"')
    
    return "\n".join(asm)