import os
import struct
import sys

def patch_elf(path):
    print(f"Checking {path}...")
    
    if not os.path.exists(path):
        print("❌ File not found.")
        return False

    with open(path, "r+b") as f:
        # 1. Read Magic to verify ELF
        f.seek(0)
        magic = f.read(4)
        if magic != b'\x7fELF':
            print("❌ Not an ELF file.")
            return False

        # 2. Read Class (32-bit or 64-bit)
        ei_class = struct.unpack("B", f.read(1))[0] # 1 = 32-bit, 2 = 64-bit
        
        # 3. Read Endianness
        ei_data = struct.unpack("B", f.read(1))[0] # 1 = Little, 2 = Big
        endian = "<" if ei_data == 1 else ">"
        
        print(f"Detected: {'32-bit' if ei_class == 1 else '64-bit'} {'Little' if ei_data == 1 else 'Big'}-Endian")

        if ei_class == 1: # 32-bit
            # Header offsets for 32-bit
            # e_phoff @ 28 (4 bytes)
            # e_phentsize @ 42 (2 bytes)
            # e_phnum @ 44 (2 bytes)
            f.seek(28)
            e_phoff = struct.unpack(f"{endian}I", f.read(4))[0]
            f.seek(42)
            e_phentsize = struct.unpack(f"{endian}H", f.read(2))[0]
            f.seek(44)
            e_phnum = struct.unpack(f"{endian}H", f.read(2))[0]
            
            p_type_fmt = f"{endian}I"
            p_flags_offset_from_header = 24 # In 32-bit, p_flags is at offset 24 (after p_filesz, p_memsz)
            # WAIT! 32-bit Phdr layout:
            # p_type (4), p_offset (4), p_vaddr (4), p_paddr (4), p_filesz (4), p_memsz (4), p_flags (4), p_align (4)
            p_flags_pos = 24

        else: # 64-bit
            # Header offsets for 64-bit
            # e_phoff @ 32 (8 bytes)
            # e_phentsize @ 54 (2 bytes)
            # e_phnum @ 56 (2 bytes)
            f.seek(32)
            e_phoff = struct.unpack(f"{endian}Q", f.read(8))[0]
            f.seek(54)
            e_phentsize = struct.unpack(f"{endian}H", f.read(2))[0]
            f.seek(56)
            e_phnum = struct.unpack(f"{endian}H", f.read(2))[0]
            
            p_type_fmt = f"{endian}I"
            # 64-bit Phdr layout:
            # p_type (4), p_flags (4), p_offset (8), ...
            p_flags_pos = 4 

        print(f"Header Info: Offset={e_phoff}, Count={e_phnum}, Size={e_phentsize}")

        if e_phoff == 0 or e_phnum == 0:
             print("❌ Invalid header info.")
             return False

        # Iterate Program Headers
        for i in range(e_phnum):
            header_start = e_phoff + (i * e_phentsize)
            f.seek(header_start)
            
            # Read p_type
            p_type = struct.unpack(p_type_fmt, f.read(4))[0]
            
            # PT_GNU_STACK = 0x6474e551
            if p_type == 0x6474e551:
                print("Found PT_GNU_STACK header.")
                
                # Seek to flags
                f.seek(header_start + p_flags_pos)
                p_flags_val = struct.unpack(f"{endian}I", f.read(4))[0]
                
                print(f"Current flags: {hex(p_flags_val)}")
                
                if p_flags_val & 1: # Check if Executable bit is set (PF_X = 1)
                    print("⚠️ Stack is marked executable. Patching...")
                    new_flags = p_flags_val & ~1 # Clear executable bit
                    
                    # Go back and write
                    f.seek(header_start + p_flags_pos)
                    f.write(struct.pack(f"{endian}I", new_flags))
                    print(f"✅ Patched flags to: {hex(new_flags)}")
                else:
                    print("✅ Stack is ALREADY non-executable. No fix needed.")
                return True

    print("❌ Could not find PT_GNU_STACK header.")
    return False

# Paths to check based on your error logs
paths_to_try = [
    "/home/pi/.local/lib/python3.13/site-packages/vosk/libvosk.so",
    "/home/pi/.local/lib/python3.10/site-packages/vosk/libvosk.so",
    # Add potential 32-bit paths just in case
    "/usr/lib/arm-linux-gnueabihf/libvosk.so"
]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        paths_to_try = [sys.argv[1]]

    success = False
    for p in paths_to_try:
        try:
             # Basic sanity check before patching
             if os.path.exists(p):
                 if patch_elf(p):
                     success = True
                     break
        except Exception as e:
            print(f"Error checking {p}: {e}")
            
    if not success:
        print("\n❌ Failed to patch automatically.")
        print("Try running: python3 fix_vosk.py /exact/path/to/libvosk.so")
