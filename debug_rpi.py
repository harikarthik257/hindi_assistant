import platform
import os
import subprocess
import sys

def run_cmd(cmd):
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return output.decode().strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output.decode().strip()}"

print("----------- DIY DIAGNOSTICS -----------")

# 1. Check Architecture
arch = platform.machine()
print(f"1. System Architecture: {arch}")
if "aarch64" in arch:
    print("   ✅ You are on 64-bit (Good for the files I gave you).")
elif "armv7" in arch:
    print("   ⚠️ You are on 32-bit! The Piper I gave you (aarch64) WILL NOT WORK.")
    print("      We need to download the armv7 version.")
else:
    print(f"   ℹ️ Unknown architecture: {arch}")

# 2. Check Piper File
piper_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "piper", "piper")
print(f"\n2. Checking Piper Path: {piper_path}")

if os.path.exists(piper_path):
    print("   ✅ File exists.")
    
    # Check permissions
    if os.access(piper_path, os.X_OK):
        print("   ✅ File is executable.")
    else:
        print("   ❌ File is NOT executable. (Run 'chmod +x piper/piper')")

    # Check file type
    print(f"   ℹ️ File Type: {run_cmd(f'file {piper_path}')}")
    
    # Try running it
    print("\n3. Trying to run Piper --version:")
    print(run_cmd(f"{piper_path} --version"))

else:
    print("   ❌ File DOES NOT EXIST.")
    print("   Did you extract it correctly? Is it in a subfolder?")
    print("   Listing contents of 'piper' folder:")
    piper_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "piper")
    if os.path.exists(piper_dir):
         print(run_cmd(f"ls -R {piper_dir}"))
    else:
         print("   ❌ 'piper' folder is missing too!")

print("---------------------------------------")
