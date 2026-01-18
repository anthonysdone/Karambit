import sys
from basic import *
from asm import *
from cpu import *
from osys import *

def main():
    if len(sys.argv) < 2:
        print("Usage: python run.py <file.tb|file.asm> [--debug]")
        sys.exit(1)

    filename = sys.argv[1]
    debug = "--debug" in sys.argv

    if debug:
        print(f"\nStarting execution:")

    with open(filename, "r") as f:
        source = f.read()
        if debug:
            print(f"\nLoaded {filename}")

    if filename.endswith(".tb"):
        asm_text = compile_basic(source)
        if debug:
            print("\nCompiled assembly:")
            print(asm_text)
    else:
        asm_text = source

    origin, blob, entry = assemble(asm_text)

    if debug:
        print(f"\nAssembled:")
        print(f"Origin: 0x{origin:04X}")
        print(f"Entry:  0x{entry:04X}")
        print(f"Size:   {len(blob)} bytes")

    mem = bytearray(65536)
    mem[origin:origin + len(blob)] = blob

    osys = OSys()
    cpu = CPU(mem, entry, osys)
    cpu.debug = debug
    
    if debug:
        print(f"\nCPU execution:")
        print(f"Entry point: 0x{entry:04X}")

    try: 
        cpu.run()
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"\nError: {e}")
        if debug:
            print(f"PC:   0x{cpu.pc:04X}")
            print(f"Regs: {cpu.regs}")
            print(f"Z:    {cpu.z}")
        sys.exit(1)
    
if __name__ == "__main__":
    main()
