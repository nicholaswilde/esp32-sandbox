#!/usr/bin/env python3
"""
Patch script for google-colab-cli v0.6.0 KernelClient AttributeError.

Resolves:
AttributeError: module 'jupyter_kernel_client' has no attribute 'KernelClient'
"""

import glob
import os
import sys
from pathlib import Path


def find_site_packages_dirs() -> list[Path]:
    dirs = []
    # 1. uv tool directory
    uv_base = Path.home() / ".local" / "share" / "uv" / "tools" / "google-colab-cli"
    for sp in uv_base.glob("lib/python*/site-packages"):
        if sp.is_dir():
            dirs.append(sp)

    # 2. current environment site-packages
    for p in sys.path:
        path_obj = Path(p)
        if path_obj.name == "site-packages" and path_obj.is_dir():
            dirs.append(path_obj)

    # Deduplicate
    unique_dirs = []
    seen = set()
    for d in dirs:
        resolved = d.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_dirs.append(resolved)
    return unique_dirs


def patch_jupyter_kernel_client(sp_dir: Path) -> bool:
    init_file = sp_dir / "jupyter_kernel_client" / "__init__.py"
    if not init_file.exists():
        return False

    content = init_file.read_text(encoding="utf-8")
    if "KernelClient = JupyterKernelClient" in content:
        print(f"[patch] jupyter_kernel_client already patched: {init_file}")
        return True

    target = "from jupyter_kernel_client.client import JupyterKernelClient\n"
    if target in content:
        new_content = content.replace(
            target,
            target + "KernelClient = JupyterKernelClient\n",
        )
        init_file.write_text(new_content, encoding="utf-8")
        print(f"[patch] Successfully patched jupyter_kernel_client: {init_file}")
        return True

    print(f"[patch] Warning: target import not found in {init_file}")
    return False


def patch_colab_cli(sp_dir: Path) -> bool:
    runtime_file = sp_dir / "colab_cli" / "runtime.py"
    if not runtime_file.exists():
        return False

    content = runtime_file.read_text(encoding="utf-8")
    if "_kernel_client_cls = getattr" in content:
        print(f"[patch] colab_cli/runtime.py already patched: {runtime_file}")
        return True

    target = "self._kernel_client = jupyter_kernel_client.KernelClient("
    replacement = (
        "_kernel_client_cls = getattr(\n"
        "                        jupyter_kernel_client, 'KernelClient', getattr(jupyter_kernel_client, 'JupyterKernelClient', None)\n"
        "                    )\n"
        "                    self._kernel_client = _kernel_client_cls("
    )

    if target in content:
        new_content = content.replace(target, replacement)
        runtime_file.write_text(new_content, encoding="utf-8")
        print(f"[patch] Successfully patched colab_cli: {runtime_file}")
        return True

    print(f"[patch] Warning: target pattern not found in {runtime_file}")
    return False


def main():
    sp_dirs = find_site_packages_dirs()
    if not sp_dirs:
        print("[patch] Error: could not find site-packages directory for google-colab-cli")
        sys.exit(1)

    patched_any = False
    for sp in sp_dirs:
        p1 = patch_jupyter_kernel_client(sp)
        p2 = patch_colab_cli(sp)
        if p1 or p2:
            patched_any = True

    if patched_any:
        print("[patch] google-colab-cli patch complete.")
    else:
        print("[patch] No patchable files found.")


if __name__ == "__main__":
    main()
