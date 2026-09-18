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

def patch_colab_token_refresh(sp_dir: Path) -> bool:
    common_file = sp_dir / "colab_cli" / "common.py"
    if not common_file.exists():
        return False

    content = common_file.read_text(encoding="utf-8")
    if "assignment_by_endpoint = {a.endpoint: a for a in assignments}" in content:
        print(f"[patch] colab_cli/common.py already patched for token refresh: {common_file}")
        return True

    target_sync = (
        "        assignments = self.client.list_assignments()\n"
        "        active_endpoints = {a.endpoint for a in assignments}\n"
        "\n"
        "        self._sessions = local_sessions\n"
        "        pruned = 0\n"
        "        for name, s in list(self._sessions.items()):\n"
        "            if s.endpoint not in active_endpoints:\n"
        "                self.prune_session(name)\n"
        "                pruned += 1"
    )
    replacement_sync = (
        "        assignments = self.client.list_assignments()\n"
        "        assignment_by_endpoint = {a.endpoint: a for a in assignments}\n"
        "\n"
        "        self._sessions = local_sessions\n"
        "        pruned = 0\n"
        "        for name, s in list(self._sessions.items()):\n"
        "            if s.endpoint not in assignment_by_endpoint:\n"
        "                self.prune_session(name)\n"
        "                pruned += 1\n"
        "            else:\n"
        "                a = assignment_by_endpoint[s.endpoint]\n"
        "                if s.token != a.runtime_proxy_info.token or s.url != a.runtime_proxy_info.url:\n"
        "                    s.token = a.runtime_proxy_info.token\n"
        "                    s.url = a.runtime_proxy_info.url\n"
        "                    self.store.add(s)"
    )

    target_resolve = (
        "    def resolve_session(self, session_name: Optional[str]) -> str:\n"
        "        if session_name:\n"
        "            return session_name"
    )
    replacement_resolve = (
        "    def resolve_session(self, session_name: Optional[str]) -> str:\n"
        "        if session_name:\n"
        "            s = self.store.get(session_name)\n"
        "            if s and s.token:\n"
        "                try:\n"
        "                    import base64, json, time\n"
        "                    p = s.token.split('.')[1]\n"
        "                    p += '=' * (-len(p) % 4)\n"
        "                    exp = json.loads(base64.urlsafe_b64decode(p.encode('ascii'))).get('exp', 0)\n"
        "                    if time.time() >= exp - 120:\n"
        "                        self.sync_sessions()\n"
        "                except Exception:\n"
        "                    pass\n"
        "            return session_name"
    )

    if target_sync in content and target_resolve in content:
        new_content = content.replace(target_sync, replacement_sync).replace(target_resolve, replacement_resolve)
        common_file.write_text(new_content, encoding="utf-8")
        print(f"[patch] Successfully patched colab_cli token refresh: {common_file}")
        return True

    print(f"[patch] Warning: sync/resolve targets not found in {common_file}")
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
        p3 = patch_colab_token_refresh(sp)
        if p1 or p2 or p3:
            patched_any = True

    if patched_any:
        print("[patch] google-colab-cli patch complete.")
    else:
        print("[patch] No patchable files found.")


if __name__ == "__main__":
    main()

