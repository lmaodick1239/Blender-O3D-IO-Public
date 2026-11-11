"""Exercise verifier behavior in a disposable copy of the current checkout."""
import io
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
TASK3 = Path("docs/research/evidence/o3d-export-fidelity/task-3")
LEDGER = Path("docs/research/2026-11-10-o3d-export-fidelity.md")


def run(*args, cwd, check=True):
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True)


def main():
    with tempfile.TemporaryDirectory(prefix="task3-verifier-") as temporary:
        fixture = Path(temporary)
        archive = subprocess.run(["git", "archive", "--format=tar", "HEAD"], cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
            bundle.extractall(fixture, filter="data")
        shutil.copytree(ROOT / TASK3, fixture / TASK3, dirs_exist_ok=True)
        shutil.copy2(ROOT / LEDGER, fixture / LEDGER)

        run("git", "init", "-q", cwd=fixture)
        run("git", "config", "user.email", "task3-test@example.invalid", cwd=fixture)
        run("git", "config", "user.name", "Task 3 verifier test", cwd=fixture)
        run("git", "add", "-f", "-A", cwd=fixture)
        run("git", "commit", "-qm", "fixture", cwd=fixture)
        result = run("python3", "-B", str(TASK3 / "verify-evidence.py"), "--write-report", cwd=fixture, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        run("git", "add", "-f", "-A", cwd=fixture)
        run("git", "commit", "--amend", "-qm", "fixture with report", cwd=fixture)

        ledger = fixture / LEDGER
        ledger.write_text(ledger.read_text() + "\nTemporary future ledger note.\n")
        source = fixture / "o3d_io/io_o3d_export.py"
        source.write_text(source.read_text() + "\n# unrelated future implementation change\n")
        result = run("python3", "-B", str(TASK3 / "verify-evidence.py"), cwd=fixture, check=False)
        assert result.returncode == 0, result.stdout + result.stderr

        evidence = fixture / TASK3 / "reader-fields.asm"
        evidence.write_bytes(evidence.read_bytes() + b"\ncorruption\n")
        result = run("python3", "-B", str(TASK3 / "verify-evidence.py"), cwd=fixture, check=False)
        assert result.returncode != 0, "immutable retained-artifact corruption was accepted"
        assert "retained_bytes" in result.stderr or "retained_sha256" in result.stderr, result.stderr
    print("VERIFY_EVIDENCE_REGRESSION_OK mutable_state=accepted immutable_corruption=rejected")


if __name__ == "__main__":
    main()
