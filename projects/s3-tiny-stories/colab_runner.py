#!/usr/bin/env python3
"""
Host-side runner for building/training s3-tiny-stories on Google Colab (Free Tier).

Integrates with the `colab` CLI to provision free-tier T4 GPU (or CPU) sessions,
upload local workspace payloads, execute remote builds/training, download generated
INT4 model binaries, and automatically clean up VM compute resources.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

SESSION_DEFAULT = "s3-stories"
PROJECT_DIR = Path(__file__).resolve().parent


def log(msg: str):
    print(f"[colab-runner] {msg}", flush=True)


def run_cmd(cmd: list[str], check: bool = True, capture_output: bool = False, timeout: float | None = None) -> subprocess.CompletedProcess:
    log(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, text=True, capture_output=capture_output, timeout=timeout)


def check_colab_cli() -> bool:
    if shutil.which("colab") is None:
        log("ERROR: 'colab' CLI is not found in PATH.")
        log("Install it via: uv tool install google-colab-cli")
        return False
    return True


def check_auth() -> bool:
    if not check_colab_cli():
        return False

    # Check if OAuth token or ADC is valid without hanging on interactive prompt
    try:
        res = subprocess.run(
            ["colab", "sessions"],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=5,
        )
        if res.returncode == 0:
            log("Authentication verified successfully!")
            return True
    except (subprocess.TimeoutExpired, Exception):
        pass

    log("Authentication required for Google Colab CLI.")
    log("Please run this one-time authorization command in your interactive terminal:")
    log("    colab sessions")
    log("or if using Application Default Credentials (ADC):")
    log("    gcloud auth application-default login --scopes=openid,https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/colaboratory")
    return False


def start_session(session_name: str, force_cpu: bool = False) -> bool:
    """Start a free-tier Colab VM session (attempts T4 GPU, falls back to CPU)."""
    if not force_cpu:
        log(f"Attempting to provision Free-Tier T4 GPU session: '{session_name}'...")
        res = subprocess.run(["colab", "new", "-s", session_name, "--gpu", "T4"], capture_output=True, text=True)
        if res.returncode == 0:
            log(f"Successfully provisioned T4 GPU session '{session_name}'.")
            return True
        log(f"T4 GPU allocation not available or quota reached: {res.stderr.strip()}")
        log("Falling back to Free-Tier standard CPU runtime...")

    res = subprocess.run(["colab", "new", "-s", session_name], capture_output=True, text=True)
    if res.returncode == 0:
        log(f"Successfully provisioned Free-Tier CPU session '{session_name}'.")
        return True
    log(f"Failed to start Colab session: {res.stderr.strip()}")
    return False


def stop_session(session_name: str):
    """Stop the Colab session to release free-tier compute resources."""
    log(f"Stopping session '{session_name}'...")
    subprocess.run(["colab", "stop", "-s", session_name], check=False)


def create_payload_tar(tar_path: Path):
    """Create a lightweight payload tarball excluding large binaries and caches."""
    log(f"Creating project payload at {tar_path}...")
    exclude_dirs = {".venv", "__pycache__", ".git", ".pio", "data"}
    exclude_exts = {".bin", ".pt", ".o", ".a"}

    def filter_tar(tarinfo):
        path_parts = Path(tarinfo.name).parts
        if any(part in exclude_dirs for part in path_parts):
            return None
        if Path(tarinfo.name).suffix in exclude_exts:
            return None
        return tarinfo

    with tarfile.open(tar_path, "w:gz") as tar:
        for item in ["research", "pc_tools", "colab_remote_task.py"]:
            src = PROJECT_DIR / item
            if src.exists():
                tar.add(src, arcname=item, filter=filter_tar)


def execute_build(
    session_name: str,
    action: str,
    keep_session: bool,
    force_cpu: bool,
    timeout: int | None = None,
):
    if not check_auth():
        sys.exit(1)

    if timeout is None:
        if action == "train-full":
            timeout = 14400  # 4 hours
        elif action == "train-test":
            timeout = 3600   # 1 hour
        else:
            timeout = 1800   # 30 mins

    # Auto-heal google-colab-cli KernelClient AttributeError if needed
    try:
        import patch_colab_cli
        patch_colab_cli.main()
    except Exception as e:
        log(f"Notice: patch check skipped: {e}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tar_path = Path(tmpdir) / "payload.tar.gz"
        create_payload_tar(tar_path)

        # Check if session is already running
        status_res = subprocess.run(["colab", "status", "-s", session_name], capture_output=True, text=True)
        session_exists = status_res.returncode == 0 and "not found" not in status_res.stdout.lower()

        if not session_exists:
            if not start_session(session_name, force_cpu=force_cpu):
                sys.exit(1)
        else:
            log(f"Using existing session '{session_name}'.")

        try:
            # Upload payload and remote runner
            log("Uploading payload to Colab VM...")
            run_cmd(["colab", "upload", "-s", session_name, str(tar_path), "/content/payload.tar.gz"])
            run_cmd(["colab", "upload", "-s", session_name, str(PROJECT_DIR / "colab_remote_task.py"), "/content/colab_remote_task.py"])

            # Execute remote task with streaming output
            log(f"Executing remote action: {action} (timeout: {timeout}s)...")
            status_file = "/content/output/status.txt"
            exec_code = (
                "import os, subprocess, sys\n"
                f"if os.path.exists('{status_file}'):\n"
                f"    os.remove('{status_file}')\n"
                f"p = subprocess.Popen([sys.executable, '-u', '/content/colab_remote_task.py', '--action', '{action}'], "
                "stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)\n"
                "for line in p.stdout:\n"
                "    sys.stdout.write(line)\n"
                "    sys.stdout.flush()\n"
                "p.wait()\n"
                "if p.returncode == 0:\n"
                f"    with open('{status_file}', 'w') as f:\n"
                "        f.write('SUCCESS\\n')\n"
                "else:\n"
                f"    raise RuntimeError(f'Remote action {action} failed with exit code {{p.returncode}}')\n"
            )
            proc = subprocess.Popen(
                ["colab", "exec", "-s", session_name, "--timeout", str(timeout)],
                stdin=subprocess.PIPE,
                text=True,
            )
            proc.communicate(input=exec_code)
            if proc.returncode != 0:
                log(f"Remote execution failed with exit code {proc.returncode}")
                sys.exit(proc.returncode)

            # Verify remote success status before downloading artifacts
            status_local = Path(tmpdir) / "status.txt"
            res = subprocess.run(
                ["colab", "download", "-s", session_name, status_file, str(status_local)],
                capture_output=True,
                text=True,
            )
            if res.returncode != 0 or not status_local.exists() or "SUCCESS" not in status_local.read_text():
                log(f"Remote action '{action}' failed on Colab VM (missing success confirmation).")
                sys.exit(1)

            # Download staged artifacts back to local repository
            log("Downloading artifacts from Colab VM...")
            if action == "quantize":
                out_local = PROJECT_DIR / "pc_tools" / "stories15M_q4.bin"
                run_cmd(["colab", "download", "-s", session_name, "/content/output/stories15M_q4.bin", str(out_local)])
                log(f"Quantized model saved to: {out_local} ({out_local.stat().st_size:,} bytes)")

                # Download vocab if updated
                vocab_local = PROJECT_DIR / "src" / "generated" / "vocab.h"
                try:
                    run_cmd(["colab", "download", "-s", session_name, "/content/output/vocab.h", str(vocab_local)])
                    log(f"Vocabulary header saved to: {vocab_local}")
                except Exception:
                    pass
            else:
                art_dir = PROJECT_DIR / "artifacts" / "tinystories"
                art_dir.mkdir(parents=True, exist_ok=True)
                tag = "ple_v32768_c15000000_s0.bin" if action == "train-full" else "ple_v32768_c1500000_s0.bin"
                out_local = art_dir / tag
                run_cmd(["colab", "download", "-s", session_name, f"/content/output/{tag}", str(out_local)])
                log(f"Custom trained model saved to: {out_local} ({out_local.stat().st_size:,} bytes)")

                # Also download references if available
                for ref_name in ("model.bin", "tokenizer.json", "golden.txt"):
                    try:
                        run_cmd(["colab", "download", "-s", session_name, f"/content/output/{ref_name}", str(art_dir / ref_name)], check=False)
                    except Exception:
                        pass

            log("Build finished successfully! Ready to flash to ESP32-S3 via 'task flash-model'.")

        finally:
            if not keep_session:
                stop_session(session_name)
            else:
                log(f"Session '{session_name}' kept alive. Remember to run 'colab stop -s {session_name}' when done.")


def main():
    parser = argparse.ArgumentParser(description="Google Colab Runner for s3-tiny-stories")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Auth check
    subparsers.add_parser("check-auth", help="Verify colab CLI authentication")

    # Start session
    start_p = subparsers.add_parser("start-session", help="Start a Colab VM session")
    start_p.add_argument("-s", "--session", default=SESSION_DEFAULT, help="Session name")
    start_p.add_argument("--cpu", action="store_true", help="Force CPU instead of T4 GPU")

    # Stop session
    stop_p = subparsers.add_parser("stop-session", help="Stop a Colab VM session")
    stop_p.add_argument("-s", "--session", default=SESSION_DEFAULT, help="Session name")

    # Build / Train
    build_p = subparsers.add_parser("build", help="Run build/train task on Colab")
    build_p.add_argument(
        "--action",
        choices=["quantize", "train-test", "train-full"],
        default="quantize",
        help="Action to perform on Colab (default: quantize)",
    )
    build_p.add_argument("-s", "--session", default=SESSION_DEFAULT, help="Session name")
    build_p.add_argument("--keep", action="store_true", help="Keep VM session running after task finishes")
    build_p.add_argument("--cpu", action="store_true", help="Force CPU instead of T4 GPU")
    build_p.add_argument("--timeout", type=int, default=None, help="Execution timeout in seconds")

    args = parser.parse_args()

    if args.command == "check-auth":
        check_auth()
    elif args.command == "start-session":
        start_session(args.session, force_cpu=args.cpu)
    elif args.command == "stop-session":
        stop_session(args.session)
    elif args.command == "build":
        execute_build(args.session, args.action, args.keep, args.cpu, args.timeout)


if __name__ == "__main__":
    main()
