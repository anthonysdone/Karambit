# Karambit - Complete Design Specification

**Target:** <1000 Lines of Code (Python 3, stdlib only)  
**Purpose:** Educational VM for absolute beginners to build interactive terminal programs

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [File Structure](#3-file-structure)
4. [basicPU Specification](#4-basicpu-specification)
5. [Memory Map](#5-memory-map)
6. [Assembler Specification](#6-assembler-specification)
7. [Operating System / Syscalls](#7-operating-system--syscalls)
8. [basic Language](#8-basic-language)
9. [Compiler Design](#9-compiler-design)
10. [Runtime System](#10-runtime-system)
11. [Example Programs](#11-example-programs)
12. [Implementation Guidelines](#12-implementation-guidelines)

---

## 1. Project Overview

### 1.1 Goals

- Create a complete "language → bytecode → CPU → OS" pipeline in under 1000 LOC
- Enable absolute beginners to write interactive terminal programs
- Use only Python 3 standard library (maximum portability)
- Keep every component simple enough to understand in one sitting

### 1.2 Key Design Principles

**Simplicity over features:**
- Label-based control flow (simple, no line number tracking)
- Restricted expression grammar (6 patterns only)
- Fixed instruction encoding (no variable-length complexity)
- Blocking keyboard input (portable across all platforms)

**Educational focus:**
- Every instruction is 1-4 bytes (easy to understand)
- OS provides interactive program primitives (screen buffer, timing, input)
- Compilation is template-based (pattern matching, not AST walking)

**LOC Budget Allocation:**
- `isa.py`: ~50 LOC (constants and tables)
- `cpu.py`: ~150 LOC (fetch-decode-execute loop)
- `asm.py`: ~250 LOC (two-pass assembler)
- `osys.py`: ~120 LOC (syscall implementations)
- `basic.py`: ~200 LOC (basic compiler)
- `run.py`: ~50 LOC (CLI and loader)
- **Total: ~820 LOC**

---

## 2. Architecture

```
┌─────────────┐
│  .tb file  │  BASIC source
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  basic.py   │  Compiler: .tb → .asm
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  .asm file  │  Assembly source
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   asm.py    │  Assembler: .asm → bytecode
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   memory    │  64KB byte array
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   cpu.py    │  Executes bytecode ←→ osys.py (syscalls)
└─────────────┘
```

### 2.1 Data Flow

1. **Compile phase:**
   - Parse basic line by line
   - Emit assembly templates for each statement
   - Generate string pool at fixed address

2. **Assemble phase:**
   - Two-pass: collect labels, then emit bytes
   - Resolve label references
   - Output: (origin, blob, entrypoint)

3. **Load phase:**
   - Copy blob into 64KB memory array
   - Initialize CPU registers and OS state

4. **Execute phase:**
   - CPU fetch-decode-execute loop
   - SYS instructions call OS handlers
   - HLT stops execution

---

## 3. File Structure

```
basic_vm/
├── isa.py       # Instruction set constants and opcode map
├── cpu.py       # Bytecode interpreter
├── asm.py       # Two-pass assembler
├── osys.py      # Operating system and syscalls
├── basic.py     # basic to assembly compiler
└── run.py       # CLI entry point
```

### 3.1 Module Dependencies

```
run.py
  ├─→ basic.py → asm.py → isa.py
  └─→ cpu.py → osys.py → isa.py
```

No circular dependencies. Each module has a single, clear responsibility.

---

## 4. basicPU Specification

### 4.1 CPU State

```python
class CPU:
    regs: list[int]  # [R0, R1, R2, R3] each 0..255
    pc: int          # Program counter 0..65535
    z: bool          # Zero flag
    mem: bytearray   # 64KB memory
    running: bool    # Execution state
```

### 4.2 Registers

- **R0, R1, R2, R3:** General-purpose 8-bit registers
- **PC:** 16-bit program counter
- **Z:** Zero/equality flag (set by CMP instructions)

Register encoding: `R0=0, R1=1, R2=2, R3=3`

### 4.3 Address Encoding

Little-endian 16-bit addresses:
```
[lo_byte, hi_byte]
address = lo + 256 * hi
```

### 4.4 Instruction Set (15 instructions)

#### Data Movement

| Opcode | Mnemonic | Bytes | Operation |
|--------|----------|-------|-----------|
| 0x10 | `LDI r, imm` | `[0x10, r, imm]` | `R[r] = imm` |
| 0x11 | `LDM r, addr` | `[0x11, r, lo, hi]` | `R[r] = mem[addr]` |
| 0x12 | `STM r, addr` | `[0x12, r, lo, hi]` | `mem[addr] = R[r]` |
| 0x13 | `MOV rd, rs` | `[0x13, rd, rs]` | `R[rd] = R[rs]` |

#### Arithmetic (8-bit wraparound)

| Opcode | Mnemonic | Bytes | Operation |
|--------|----------|-------|-----------|
| 0x20 | `ADD rd, rs` | `[0x20, rd, rs]` | `R[rd] = (R[rd] + R[rs]) & 0xFF` |
| 0x21 | `ADDI r, imm` | `[0x21, r, imm]` | `R[r] = (R[r] + imm) & 0xFF` |
| 0x22 | `SUB rd, rs` | `[0x22, rd, rs]` | `R[rd] = (R[rd] - R[rs]) & 0xFF` |
| 0x23 | `SUBI r, imm` | `[0x23, r, imm]` | `R[r] = (R[r] - imm) & 0xFF` |

#### Comparison & Branching

| Opcode | Mnemonic | Bytes | Operation |
|--------|----------|-------|-----------|
| 0x30 | `CMP ra, rb` | `[0x30, ra, rb]` | `Z = (R[ra] == R[rb])` |
| 0x34 | `CMPI r, imm` | `[0x34, r, imm]` | `Z = (R[r] == imm)` |
| 0x31 | `JMP addr` | `[0x31, lo, hi]` | `PC = addr` |
| 0x32 | `JZ addr` | `[0x32, lo, hi]` | `if Z: PC = addr` |
| 0x33 | `JNZ addr` | `[0x33, lo, hi]` | `if not Z: PC = addr` |

#### System

| Opcode | Mnemonic | Bytes | Operation |
|--------|----------|-------|-----------|
| 0x40 | `SYS imm` | `[0x40, imm]` | Call OS syscall #imm |
| 0xFF | `HLT` | `[0xFF]` | Stop execution |

### 4.5 Execution Rules

1. **Fetch:** Read opcode at PC
2. **Decode:** Determine instruction length and operands
3. **Execute:** Perform operation
4. **Advance:** Increment PC by instruction length (unless jump occurred)

**Error handling:**
- Unknown opcode → `RuntimeError("illegal opcode 0x{:02X} at PC=0x{:04X}")`
- PC out of bounds → stop execution

**SYS instruction:**
- Calls `osys.handle(sysno, regs, mem)` where `regs` is the mutable register list
- OS can modify registers to return values

---

## 5. Memory Map

### 5.1 Layout

```
0x0000 - 0x00FF   Zero page (256 bytes, unused in this design)
0x0100 - 0x0119   Variables A-Z (26 bytes)
0x011A - 0x01FF   Reserved (230 bytes)
0x0200 - 0x2FFF   Code segment (~11KB)
0x3000 - 0xFFFF   String pool and data (~52KB)
```

### 5.2 Variable Addresses

Variables are single-letter A-Z, stored contiguously:

```python
def var_addr(var_char: str) -> int:
    return 0x0100 + (ord(var_char) - ord('A'))
```

Examples:
- `A` → `0x0100`
- `B` → `0x0101`
- `Z` → `0x0119`

### 5.3 Constants

```python
VAR_BASE = 0x0100
CODE_ORG = 0x0200
STR_ORG = 0x3000
```

---

## 6. Assembler Specification

### 6.1 Input Format

Assembly language consists of:
- **Instructions:** `LDI R0, 42`
- **Directives:** `.org 0x0200`, `.byte 123`, `.word 0x1234`, `.string "text"`
- **Labels:** `loop:`, `start:`
- **Comments:** `;` to end of line

### 6.2 Lexical Rules

**Tokenization:**
1. Strip comments (everything after `;`)
2. Replace commas with spaces
3. Split on whitespace
4. Ignore blank lines

**Labels:**
- Format: `[A-Za-z_][A-Za-z0-9_]*:`
- Can appear alone on a line or before an instruction
- Label value = current assembly address

**Numbers:**
- Decimal: `123`
- Hexadecimal: `0x1A`, `0x1a`
- Range validation: 0-255 for bytes, 0-65535 for words

### 6.3 Directives

#### `.org N`
Set current assembly address to N.

```assembly
.org 0x0200
start:
  LDI R0, 65
```

#### `.byte N`
Emit a single byte.

```assembly
.byte 0xFF
.byte 42
```

#### `.word N`
Emit a 16-bit word (little-endian).

```assembly
.word 0x1234   ; emits [0x34, 0x12]
```

#### `.string "string"`
Emit string bytes followed by null terminator.

```assembly
msg: .string "Hello\n"   ; emits [72, 101, 108, 108, 111, 10, 0]
```

**String escape sequences:**
- `\"` → `"`
- `\\` → `\`
- `\n` → newline (10)
- Any other `\X` → error

### 6.4 Two-Pass Assembly

**Pass 1: Symbol collection**
- Process each line
- Track current address
- Record label addresses
- Don't emit bytes yet

**Pass 2: Code generation**
- Emit bytes for each instruction/directive
- Resolve label references
- Build output blob

**Output format:**
```python
def assemble(text: str) -> tuple[int, bytes, int]:
    # Returns (origin, blob, entrypoint)
    # origin = lowest address written
    # blob = dense bytes from origin to highest address
    # entrypoint = address of start label, or first .org
```

### 6.5 Instruction Encoding Map

```python
OPCODES = {
    'LDI': 0x10,   'LDM': 0x11,   'STM': 0x12,   'MOV': 0x13,
    'ADD': 0x20,   'ADDI': 0x21,  'SUB': 0x22,   'SUBI': 0x23,
    'CMP': 0x30,   'JMP': 0x31,   'JZ': 0x32,    'JNZ': 0x33,
    'CMPI': 0x34,  'SYS': 0x40,   'HLT': 0xFF
}
```

**Encoding rules:**
- Register operand: 1 byte (0-3)
- Immediate operand: 1 byte (0-255)
- Address operand: 2 bytes little-endian (0-65535)

---

## 7. Operating System / Syscalls

### 7.1 OS State

```python
class OSys:
    # Screen buffer
    screen: list[list[int]]  # SW x SH grid of char codes
    SW: int = 40  # Screen width
    SH: int = 20  # Screen height
    
    # Keyboard buffer
    keybuf: list[int]  # Queue of character codes
```

### 7.2 Syscall Interface

```python
def handle(sysno: int, regs: list[int], mem: bytearray):
    # regs is [R0, R1, R2, R3] - mutable
    # Can modify regs[0] to return value
```

### 7.3 Syscall Catalog

#### Console I/O

**SYS 0: PUTC**
- Input: `R0 = character code`
- Effect: Print `chr(R0)` to stdout

**SYS 1: PRINTS**
- Input: `R0 = address_lo, R1 = address_hi`
- Effect: Print null-terminated string from memory

```python
addr = regs[0] + 256 * regs[1]
while mem[addr] != 0:
    print(chr(mem[addr]), end='')
    addr += 1
```

#### Screen Buffer

**SYS 2: CLS**
- Effect: Fill screen buffer with spaces (32)

**SYS 3: PUTXY**
- Input: `R0 = x, R1 = y, R2 = char`
- Effect: Set `screen[y][x] = char` (if in bounds)

**SYS 4: RENDER**
- Effect: Print screen buffer to terminal
- Implementation:
  ```python
  print('\x1b[H', end='')  # Cursor home
  for row in screen:
      print(''.join(chr(c) for c in row))
  ```

#### Timing

**SYS 5: SLEEP**
- Input: `R0 = milliseconds`
- Effect: `time.sleep(R0 / 1000.0)`

#### Keyboard Input

**SYS 6: KEY**
- Output: `R0 = character code`
- Behavior:
  1. If `keybuf` not empty: pop and return first character
  2. Else: read one line from stdin (blocking)
  3. Append line bytes + newline (10) to `keybuf`
  4. Return first character

**Design note:** Blocking behavior is intentional for simplicity and cross-platform compatibility. Programs should call KEY in appropriate places (e.g., main loop).

---

## 8. Basic Language

### 8.1 Program Structure

Programs consist of statements executed sequentially from top to bottom:

```basic
start:
  LET A = 5
  PRINT "HELLO"
  GOTO start
```

**Labels:**
- Optional labels for jump targets: `labelname:`
- Label format: `[A-Za-z_][A-Za-z0-9_]*`
- Labels can appear on their own line or before a statement
- Execution flows top-to-bottom unless redirected by GOTO/IF

### 8.2 Variables

- Single letters **A-Z** only (26 variables)
- All are unsigned bytes (0-255)
- Arithmetic wraps modulo 256
- Default value: 0

### 8.3 Expression Grammar

```
EXPR ::= NUMBER              # 42
       | VAR                 # A
       | VAR + NUMBER        # A + 5
       | VAR - NUMBER        # A - 3
       | VAR + VAR           # A + B
       | VAR - VAR           # A - B
```

**Constraints:**
- No parentheses
- No operator precedence (only one operator allowed)
- No multiplication or division
- Numbers must be 0-255

**Whitespace:** Optional around `+` and `-`

### 8.4 Conditions

```
COND ::= EXPR = EXPR        # Equality
       | EXPR <> EXPR       # Inequality
```

### 8.5 Statement Syntax

#### Comments

```basic
# Full-line comment starting with #
```

#### Assignment

```basic
LET A = 42
LET B = A + 5
LET C = A - B
```

#### Output

```basic
PRINT "Hello World\n"
PRINTC 65                # Print 'A'
PRINTC A
```

#### Control Flow

```basic
loop:
  IF A = 10 THEN GOTO done
  IF A <> B THEN GOTO check
  GOTO loop
done:
  END
```

#### Screen

```basic
CLS
PLOT 10, 5, 42          # x, y, char_code
RENDER
```

#### Timing

```basic
SLEEP 100               # Sleep 100ms
```

#### Keyboard

```basic
loop:
  KEY K                   # Read key into K
  IF K = 113 THEN GOTO quit  # 113 = 'q'
  GOTO loop
quit:
  END
```

### 8.6 Complete Statement List

| Statement | Syntax | Description |
|-----------|--------|-------------|
| REM | `REM text` | Comment |
| LET | `LET V = EXPR` | Assignment |
| PRINT | `PRINT "string"` | Print string |
| PRINTC | `PRINTC EXPR` | Print character |
| CLS | `CLS` | Clear screen |
| PLOT | `PLOT X, Y, C` | Draw to screen buffer |
| RENDER | `RENDER` | Display screen |
| SLEEP | `SLEEP MS` | Delay milliseconds |
| GOTO | `GOTO label` | Jump |
| IF | `IF COND THEN GOTO label` | Conditional jump |
| END | `END` | Halt program |
| KEY | `KEY V` | Read keyboard |

---

## 9. Compiler Design

### 9.1 Compilation Strategy

**Template-based emission:** Each BASIC statement maps to a fixed assembly template.

**No AST:** Direct pattern matching and string emission.

**Single pass:** Process statements sequentially, emit assembly, forward-reference labels resolved in assembler.

### 9.2 Parsing Process

```python
def compile(source: str) -> str:
    statements = parse_statements(source)  # Extract labels and statements
    
    asm = [".org 0x0200", "_start:"]
    strings = []
    
    for label, stmt in statements:
        if label:
            asm.append(f"{label}:")
        if stmt:
            asm.extend(compile_statement(stmt, strings))
    
    asm.append("  HLT")
    asm.append("")
    asm.append(".org 0x3000")
    asm.extend(emit_strings(strings))
    
    return '\n'.join(asm)
```

### 9.3 Expression Compilation

All expressions compile to R0:

```python
def compile_expr(expr: str) -> list[str]:
    # NUMBER
    if expr.isdigit():
        return [f"  LDI R0, {expr}"]
    
    # VAR
    if len(expr) == 1 and expr.isalpha():
        addr = 0x0100 + (ord(expr) - ord('A'))
        return [f"  LDM R0, 0x{addr:04X}"]
    
    # VAR + NUMBER
    if '+' in expr:
        var, num = expr.split('+')
        var, num = var.strip(), num.strip()
        if var.isalpha() and num.isdigit():
            addr = 0x0100 + (ord(var) - ord('A'))
            return [
                f"  LDM R0, 0x{addr:04X}",
                f"  ADDI R0, {num}"
            ]
        # VAR + VAR
        if var.isalpha() and num.isalpha():
            addr1 = 0x0100 + (ord(var) - ord('A'))
            addr2 = 0x0100 + (ord(num) - ord('A'))
            return [
                f"  LDM R0, 0x{addr1:04X}",
                f"  LDM R1, 0x{addr2:04X}",
                f"  ADD R0, R1"
            ]
    
    # Similar for VAR - NUMBER and VAR - VAR
    # ...
```

### 9.4 Statement Compilation Examples

#### LET

```basic
LET A = 5
```

Emits:
```assembly
  LDI R0, 5
  STM R0, 0x0100    ; Address of A
```

#### PRINT

```basic
PRINT "HELLO\n"
```

Emits:
```assembly
  LDI R0, 0x00      ; lo byte of str_0 address
  LDI R1, 0x30      ; hi byte (0x3000)
  SYS 1

; Later in string pool:
.org 0x3000
str_0: .asciiz "HELLO\n"
```

#### IF THEN GOTO

```basic
IF A = 5 THEN GOTO done
```

Emits:
```assembly
  LDM R0, 0x0100    ; Load A
  CMPI R0, 5
  JZ done
```

### 9.5 String Pool Management

**Sequential allocation:**

```python
str_addr = 0x3000
for i, text in enumerate(strings):
    addr = str_addr
    # Compute lo, hi bytes
    lo, hi = addr & 0xFF, addr >> 8
    # Emit load instructions with actual addresses
    str_addr += len(encode_string(text)) + 1  # +1 for null terminator
```

Compiler must compute exact addresses (not rely on assembler for label resolution in string addresses).

### 9.6 Control Flow

**Labels:** User-defined labels mark jump targets (e.g., `loop:`, `done:`).

**Sequential execution:** Statements execute top-to-bottom by default.

**Control transfers:** GOTO and IF...GOTO emit jump instructions; END emits HLT.

---

## 10. Runtime System

### 10.1 CLI Usage

```bash
# Run BASIC program
python run.py program.tb

# Run assembly program
python run.py program.asm
```

### 10.2 Execution Flow

```python
def main(filename):
    if filename.endswith('.tb'):
        source = read_file(filename)
        asm_text = compile_basic(source)
        origin, blob, entry = assemble(asm_text)
    else:
        asm_text = read_file(filename)
        origin, blob, entry = assemble(asm_text)
    
    mem = bytearray(65536)
    mem[origin:origin+len(blob)] = blob
    
    osys = OSys()
    cpu = CPU(mem, entry, osys)
    cpu.run()
```

### 10.3 CPU Execution Loop

```python
def run(self):
    self.running = True
    while self.running:
        opcode = self.mem[self.pc]
        
        if opcode == 0x10:  # LDI
            r, imm = self.mem[self.pc+1], self.mem[self.pc+2]
            self.regs[r] = imm
            self.pc += 3
        
        elif opcode == 0x40:  # SYS
            sysno = self.mem[self.pc+1]
            self.osys.handle(sysno, self.regs, self.mem)
            self.pc += 2
        
        elif opcode == 0xFF:  # HLT
            self.running = False
        
        # ... other opcodes ...
        
        else:
            raise RuntimeError(f"Illegal opcode 0x{opcode:02X} at PC=0x{self.pc:04X}")
```

---

## 11. Example Programs

### 11.1 Hello World

```basic
PRINT "HELLO WORLD\n"
END
```

### 11.2 Counter

```basic
LET A = 0
loop:
  PRINTC A + 65
  LET A = A + 1
  IF A = 26 THEN GOTO done
  GOTO loop
done:
  END
```

Prints: `ABCDEFGHIJKLMNOPQRSTUVWXYZ`

### 11.3 Interactive Cursor Movement

```basic
REM Move cursor with keyboard input
CLS
LET X = 20
LET Y = 10

mainloop:
  PLOT X, Y, 79
  RENDER
  
  KEY K
  REM W=119, S=115, A=97, D=100
  IF K = 119 THEN LET Y = Y - 1
  IF K = 115 THEN LET Y = Y + 1
  IF K = 97 THEN LET X = X - 1
  IF K = 100 THEN LET X = X + 1
  
  REM Wrap boundaries
  IF X = 255 THEN LET X = 39
  IF X = 40 THEN LET X = 0
  IF Y = 255 THEN LET Y = 19
  IF Y = 20 THEN LET Y = 0
  
  CLS
  GOTO mainloop
```

---

## 12. Implementation Guidelines

### 12.1 LOC Budget Management

**Prioritize simplicity:**
- No classes where functions suffice
- Minimal error messages
- No optimization passes
- Single-purpose functions

**Example: CPU fetch-decode-execute**

Don't do this (OOP overhead):
```python
class Instruction:
    def execute(self, cpu): ...

class LDI(Instruction): ...
```

Do this (direct dispatch):
```python
def execute_instruction(cpu, opcode):
    if opcode == 0x10: ...  # LDI
    elif opcode == 0x11: ... # LDM
```

### 12.2 Parsing Strategy

**basic compiler:**
- Use `str.split()`, `str.strip()`, `in` checks
- Pattern match with if/elif chains
- No tokenizer class, no AST nodes

**Assembler:**
- Two arrays: `labels = {}`, `code = []`
- Single loop for each pass
- Helper functions: `is_label()`, `parse_number()`, `parse_directive()`

### 12.3 Error Handling

Keep it minimal but useful:

```python
# Good: Contextual, concise
raise ValueError(f"Line {lineno}: Unknown statement '{stmt}'")

# Too much: Stack traces, recovery logic
try:
    ...
except Exception as e:
    log_error(e)
    attempt_recovery()
    ...
```

### 12.4 Code Organization

**isa.py**: Just constants, no logic
```python
OPCODES = {'LDI': 0x10, ...}
SIZES = {0x10: 3, 0x11: 4, ...}
```

**cpu.py**: Stateful executor
```python
class CPU:
    def __init__(self, mem, entry, osys): ...
    def run(self): ...
    def step(self): ...
```

**asm.py**: Pure function
```python
def assemble(text: str) -> tuple[int, bytes, int]: ...
```

**osys.py**: Stateful service object
```python
class OSys:
    def __init__(self): ...
    def handle(self, sysno, regs, mem): ...
    def _syscall_putc(self, regs): ...
```

**basic.py**: Pure function
```python
def compile_basic(source: str) -> str: ...
```

**run.py**: Thin CLI wrapper
```python
def main():
    args = parse_args()
    if args.file.endswith('.tb'): ...
```

### 12.5 Testing Strategy

**Manual testing focus:**
- Run hello world
- Run counter program
- Run interactive cursor movement
- Run cellular simulation
- Test array storage and random numbers

**Unit tests (optional, not counted in LOC):**
- Test each instruction in isolation
- Test expression compilation patterns
- Test assembler on small inputs

### 12.6 Documentation

**In-code documentation:**
- Docstrings for public functions only
- Inline comments for non-obvious bit manipulation

**External documentation:**
- This design doc
- README with quick start
- Example programs

---

## Appendix A: Complete Opcode Reference

| Hex | Mnemonic | Operands | Bytes | Description |
|-----|----------|----------|-------|-------------|
| 0x10 | LDI | r, imm | 3 | Load immediate |
| 0x11 | LDM | r, addr | 4 | Load from memory |
| 0x12 | STM | r, addr | 4 | Store to memory |
| 0x13 | MOV | rd, rs | 3 | Move register |
| 0x20 | ADD | rd, rs | 3 | Add registers |
| 0x21 | ADDI | r, imm | 3 | Add immediate |
| 0x22 | SUB | rd, rs | 3 | Subtract registers |
| 0x23 | SUBI | r, imm | 3 | Subtract immediate |
| 0x30 | CMP | ra, rb | 3 | Compare registers |
| 0x31 | JMP | addr | 3 | Unconditional jump |
| 0x32 | JZ | addr | 3 | Jump if zero |
| 0x33 | JNZ | addr | 3 | Jump if not zero |
| 0x34 | CMPI | r, imm | 3 | Compare immediate |
| 0x40 | SYS | imm | 2 | System call |
| 0xFF | HLT | - | 1 | Halt execution |

## Appendix B: Complete Syscall Reference

| # | Name | Inputs | Outputs | Description |
|---|------|--------|---------|-------------|
| 0 | PUTC | R0=char | - | Print character |
| 1 | PRINTS | R0=lo, R1=hi | - | Print string |
| 2 | CLS | - | - | Clear screen |
| 3 | PUTXY | R0=x, R1=y, R2=c | - | Plot character |
| 4 | RENDER | - | - | Display screen |
| 5 | SLEEP | R0=ms | - | Sleep milliseconds |
| 6 | KEY | - | R0=char | Read key |

---

**End of Design Document**
