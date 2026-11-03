# Paste ONLY this cell into the SAME failed Colab runtime; do not choose Run all.
# No install, model download/inference, deletion, or upload.
import sys, subprocess, importlib.metadata as metadata
from pathlib import Path
print('Python:', sys.version)
print('Executable:', sys.executable)
print('Upstream tested Python: 3.10 / 3.11; 3.13 is a risk, NOT a proven cause.')
for name in ('torch', 'torchvision', 'numpy', 'diffusers', 'transformers', 'decord', 'modelscope'):
    try: print(name, metadata.version(name))
    except metadata.PackageNotFoundError: print(name, 'NOT INSTALLED')
probe = """import torch
print('CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    p = torch.cuda.get_device_properties(0)
    print('GPU:', p.name, 'VRAM GiB:', round(p.total_memory / 2**30, 2))
"""
try:
    result = subprocess.run([sys.executable, '-c', probe], capture_output=True, text=True, timeout=30)
    print(result.stdout, result.stderr)
except subprocess.TimeoutExpired:
    print('Torch/GPU check timed out; not retried.')
print('Existing outputs:', Path('/content/ava-motion-pilot/outputs').exists(), '(do NOT delete)')
summary = Path('/content/ava-motion-pilot/failure-summary.json')
print('Saved failure:', summary.read_text() if summary.is_file() else 'None; old child error cannot be recovered from wrapper alone.')
