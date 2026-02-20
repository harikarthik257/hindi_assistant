import sounddevice as sd
try:
    print(sd.query_devices(1))
except Exception as e:
    print(f"Error querying device 1: {e}")
    print("\nAll devices:")
    print(sd.query_devices())
