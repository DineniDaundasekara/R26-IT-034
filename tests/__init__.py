import os
import sys

workspace_root = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(workspace_root) == "tests":
    workspace_root = os.path.dirname(workspace_root)
backend_dir = os.path.join(workspace_root, "backend", "python")

for p in [workspace_root, backend_dir, os.path.join(workspace_root, "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

