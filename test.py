import subprocess
import os


result = subprocess.run(
    ["osascript", "get_path.scpt"],
    capture_output=True,
    text=True
    )
result = result.stdout.strip()
subprocess.run(["open", "-R", result])