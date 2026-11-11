"""Verify this bounded research checkpoint; never execute native/Blender code.

Default is read-only. --write-report refreshes verification.json only.
--require-staged additionally requires the exact research-only staged path set
from the original checkpoint. Original ignored sources are optional cross-checks,
not public dependencies.
"""
import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PREFIX = HERE.relative_to(ROOT).as_posix()
LEDGER = ROOT / "docs/research/2026-11-10-o3d-export-fidelity.md"
BASE = "cc98cc51ec4c14903d21badf394672d394e5751f"
CHECKPOINT_LEDGER_SHA256 = "20dd67756a09e27c34b0a26b799ba16faa3008290b07bbb0e5324be3a09dd949"
TARGET = "c7765877620816dd4de4cceb21dce1996c8789c89ee550c1fb58440ee689a33e"
PIN = "a51f293548adba0dda086f5771401e8d8ab66227"
sha = lambda data: hashlib.sha256(data).hexdigest()
compact = lambda value: re.sub(r"\s+", "", value.lower())
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--write-report", action="store_true")
parser.add_argument("--require-staged", action="store_true")
args = parser.parse_args()


def git(*argv):
    process = subprocess.run(["git", *argv], cwd=ROOT, check=True, capture_output=True, text=True)
    return process.stdout


retention = json.loads((HERE / "retention.json").read_text())
assert retention["base_head"] == BASE and retention["executable_sha256"] == TARGET
assert retention["native_runtime_observations"] is False
assert retention["metadata_not_repaired"] == ["008257cc NO FUNCTION"]
files = retention["files"]
assert len({entry["path"] for entry in files}) == len(files)
local_originals_checked = 0
for entry in files:
    destination = HERE / entry["path"]
    assert destination.resolve().is_relative_to(HERE)
    raw = destination.read_bytes()
    assert len(raw) == entry["retained_bytes"] and sha(raw) == entry["retained_sha256"], destination
    assert 0 < len(raw) <= retention["limits"]["max_single_bytes"], destination
    source = ROOT / entry["source_local_only"]
    if source.is_file():
        original = source.read_bytes()
        assert len(original) == entry["source_bytes"] and sha(original) == entry["source_sha256"], source
        ranges = entry["source_lines_inclusive"]
        if ranges:
            lines = original.decode().splitlines(keepends=True)
            for lo, hi in ranges:
                assert "".join(lines[lo - 1:hi]) in raw.decode(), (destination, lo, hi)
        else:
            assert original == raw, destination
        local_originals_checked += 1
for entry in retention["local_only_worker_reports"]:
    path = ROOT / entry["local_only_path"]
    if path.is_file():
        assert sha(path.read_bytes()) == entry["sha256"] and path.stat().st_size == entry["bytes"]
status = retention["fresh_consumer_decompiler_status"]
assert len(status) == 11 and not any(item["fail_prefix"] for item in status)
assert sum(item["warning_count"] for item in status) == 313
assert all(item["exit_code"] == 0 and item["stderr"] == "" for item in retention["selected_geometry_acquisitions"])

# Success is attributed to collected job outcomes in the retained lead handoff,
# not manufactured from a quiet log or rerun through a different launcher.
lead = (HERE / "native-lead-exports.md").read_text()
for token in ["bash-9ec91a6bf7fa4b65", "bash-38b6fa2053184768", "**exit0**", "-readOnly -noanalysis", "JAVA_HOME=/home/mizuki/Downloads/jdk-27", "NO FUNCTION"]:
    assert token in lead, token
logs = {}
for name, count in [("native-authorized-seed.log", 3), ("native-authorized-consumers.log", 11)]:
    text = (HERE / name).read_text()
    exports = re.findall(r"> EXPORTED func-([0-9a-f]{8})", text)
    assert len(exports) == count and len(set(exports)) == count
    assert 'openjdk version "27"' in text and "Processing read-only project file: /1/Omsi.exe" in text
    assert "TARGET Omsi.exe SHA256 " + TARGET in text
    assert not re.search(r"^FAIL", text, re.M)
    logs[name] = {"exported_addresses": exports, "embedded_sha256": TARGET, "read_only_program": "/1/Omsi.exe", "jdk": 27, "collected_job_exit": 0, "exit_authority": "native-lead-exports.md (collected jobs); raw logs omit shell exit marker"}
assert "NO FUNCTION 008257cc" in (HERE / "native-authorized-consumers.log").read_text()
for name, end in [("history/geometry-first-attempt.log", "COMMAND_EXIT=1"), ("history/materials-first-attempt.log", "EXIT_CODE=1")]:
    text = (HERE / name).read_text()
    assert end in text and "java_home.save (Read-only file system)" in text

# Verify instruction+operand anchors, not mere mention of an address in a jump.
anchors = []
cache = {}


def anchor(name, address, *parts):
    if name not in cache:
        records = {}
        for number, line in enumerate((HERE / name).read_text().splitlines(), 1):
            match = re.match(r"\s*([0-9a-fA-F]{6,8})(?::|\s)\s*(.*)", line)
            if match:
                records[int(match.group(1), 16)] = (number, line)
        cache[name] = records
    number, line = cache[name][int(address, 16)]
    assert all(compact(part) in compact(line) for part in parts), (name, address, parts, line)
    anchors.append({"path": name, "address": address, "line": number, "instruction": line.strip(), "expected_operands": list(parts)})


for addr, offset in [("0056d41a", "[EAX]"), ("0056d422", "[EAX + 0x4]"), ("0056d42b", "[EAX + 0x8]"), ("0056d44d", "[EAX + 0xc]"), ("0056d456", "[EAX + 0x10]"), ("0056d45f", "[EAX + 0x14]"), ("0056d47e", "[EAX + 0x18]"), ("0056d484", "[EAX + 0x1c]")]:
    anchor("reader-fields.asm", addr, "MOV", offset)
anchor("reader-fields.asm", "0056db82", "MOV", "[EAX + EDX*0x4 + 0x20]")
anchor("reader-constructor-bridge.asm", "007c70be", "call", "0x56c7b4")
anchor("reader-constructor-bridge.asm", "007c7118", "mov", "[ebp-0x20]")
anchor("reader-constructor-bridge.asm", "007c711e", "call", "0x7c5a4c")
for addr, offset in [("007c5fdc", "[ESI + 0xc]"), ("007c5fe2", "[ESI + 0x10]"), ("007c5fe8", "[ESI + 0x14]"), ("007c602a", "[ESI + 0x18]")]:
    anchor("func-007c5a4c.asm", addr, "MOV", offset)
for addr, parts in [("007c5c93", ["PUSH 0x212"]), ("007c5ca2", ["CALL 0x00568010"]), ("007c6076", ["MOV ECX,0x28"]), ("007c607b", ["CALL 0x004048b4"]), ("007c6139", ["[EAX + EBX*0x4 + -0x4]"]), ("007c615c", ["CMP EBX,0x4"]), ("007c6203", ["[EAX + EBX*0x4 + -0x4]"]), ("007c622a", ["CMP EBX,0x4"]), ("007c625b", ["CALL", "[EAX + 0x60]"]), ("007c66a6", ["[EAX + 0x20]"]), ("007c66a9", ["[EDX + 0x60]"]), ("007c66b1", ["MOVSD.REP"]), ("007c668f", ["CALL 0x00568020"])]:
    anchor("func-007c5a4c.asm", addr, *parts)
for addr in ["007c6410", "007c6415", "007c641a", "007c641f"]:
    anchor("func-007c5a4c.asm", addr, "PUSH 0x3f800000")
for addr, offset in [("007c6408", "0x6c"), ("007c6452", "0x7c"), ("007c649c", "0x8c"), ("007c64e9", "0x9c"), ("007c6536", "0xac")]:
    anchor("func-007c5a4c.asm", addr, offset)
for addr, parts in [("007c7456", ["0xec"]), ("007c746a", ["0x2f"]), ("007c756a", ["CALL 0x007fc878"]), ("007c75c7", ["CALL 0x007fd9b0"]), ("007c75e8", ["CALL", "[EAX + 0x104]"]), ("007c759c", ["CALL", "[EAX + 0xc]"]), ("007c7624", ["CALL", "[EAX + 0xc]"]), ("007c765e", ["CALL", "[EAX + 0xc]"])]:
    anchor("func-007c73d4.asm", addr, *parts)
for addr in ["005fc757", "005fcc92", "005fcccc", "005fcdfb"]:
    anchor("func-005fc664.asm", addr, "CALL 0x00567e90")
anchor("func-005fdf40.asm", "005fe4e3", "CALL 0x00568020")
for addr, parts in [("005ef494", ["LEA ECX,[EBX + 0x60]"]), ("005ef499", ["[EBX + 0x198]"]), ("005ef49f", ["CALL 0x005fedc8"]), ("005ef4be", ["CALL 0x00567e98"]), ("005ef4c8", ["[EBX + 0x19c]"]), ("005ef4ce", ["CALL 0x005fedc8"])]:
    anchor("func-005ef470.asm", addr, *parts)
anchor("func-007c315c.asm", "007c316f", "LEA EDI,[EAX + 0x20]")
anchor("world-instance-bridges.asm", "005fd641", "call", "0x7c315c")
anchor("world-upload.asm", "007c3263", "call", "[eax+0xb0]")
anchor("func-007fd9b0.asm", "007fd9d0", "MOV ECX,0x2f")
anchor("func-007fd9b0.asm", "007fd9d5", "MOVSD.REP")
anchor("func-007fd9b0.asm", "007fda22", "JZ 0x007fe292")
anchor("func-007fd9b0.asm", "007fe2bd", "LEA EAX,[EBP + 0xffffff68]")
anchor("func-007fd9b0.asm", "007fe2ce", "CALL", "[EAX + 0xc4]")
for addr in ["007feb7c", "007ff195", "007fe6d7", "007fe74b"]:
    anchor("func-007fd9b0.asm", addr, "CALL 0x00800d10")
for addr, parts in [("007feb2a", ["PUSH 0x2"]), ("007feb38", ["MOV ECX,0x2"]), ("007feb47", ["PUSH 0x4"]), ("007feb55", ["MOV ECX,0x1"]), ("007feb64", ["PUSH 0x0"]), ("007feb72", ["MOV ECX,0xb"]), ("00800049", ["MOV EDX,0xab"]), ("0080005d", ["MOV EDX,0xf"]), ("0080006c", ["MOV ECX,0x80"]), ("00800080", ["MOV ECX,0x5"]), ("00800094", ["JMP 0x00800162"]), ("00800116", ["MOV ECX,0x1"]), ("0080011b", ["MOV EDX,0x1b"]), ("00800142", ["MOV EDX,0x1b"])]:
    anchor("func-007fd9b0.asm", addr, *parts)
mode1_lines = [line for address, (_, line) in cache["func-007fd9b0.asm"].items() if 0x800044 <= address <= 0x800094]
assert not any("movedx,0x1b" in compact(line) for line in mode1_lines)
anchor("func-00800d10.asm", "00800d73", "CALL", "[EAX + 0x10c]")
anchor("func-00800d80.asm", "00800db6", "CALL", "[EAX + 0xe4]")
for addr, state in [("008257db", "0x89"), ("008257f1", "0x88"), ("00825807", "0x1d")]:
    anchor("lighting-init.asm", addr, "mov", "edx," + state)
for addr in ["008257e0", "008257f6", "0082580c"]:
    anchor("lighting-init.asm", addr, "call", "0x800d80")
for addr, offset in zip(["0056d7cb", "0056d80d", "0056d850", "0056d893", "0056d8d6", "0056d919", "0056d95c", "0056d99f", "0056d9e2", "0056da25", "0056da68"], [0, 4, 8, 12, 16, 20, 24, 32, 36, 40, 48]):
    parts = ["MOV", "[EAX + EDX*0x8"]
    if offset:
        parts.append("+ 0x" + format(offset, "x") + "]")
    anchor("reader-fields.asm", addr, *parts)
for addr, offset in zip(["005f5982", "005f59ec", "005f5a56", "005f5ac0", "005f5b2a", "005f5b94", "005f5c01", "005f5c6e", "005f5cdb", "005f5d48", "005f5db5", "005f5e22", "005f5e8f", "005f5efc"], ["6c", "70", "74", "78", "7c", "80", "84", "8c", "90", "94", "9c", "a0", "a4", "ac"]):
    anchor("cfg-selected.asm", addr, "FSTP float ptr", "[EAX + 0x" + offset + "]")
anchor("cfg-selected.asm", "005f4668", "CALL 0x007c3eb0")
anchor("cfg-selected.asm", "005f46bf", "IMUL EDX,EDX,0x2f")
anchor("cfg-selected.asm", "005f46cd", "XOR EAX,EAX")
for addr in ["005f5756", "005f5807"]:
    anchor("cfg-selected.asm", addr, "MOV EDX,0x5f89e0")
anchor("matl-match.asm", "007c3f4d", "call", "0x409920")
anchor("matl-match.asm", "007c3f54", "mov", "[ebp-0x10]")
anchor("matl-match.asm", "007c3f5c", "add", "[ebp-0x10],0x1")
anchor("matl-name-normalization.asm", "004213fc", "or", "ax,0x20")
anchor("func-007fbee0.asm", "007fbf7d", "MOV byte ptr [EBX + 0x5c],AL")
for addr in ["007fc04d", "007fc197", "007fc203"]:
    anchor("func-007fbee0.asm", addr, "CALL", "+ 0xc]")

# Sources/probes were already verified by the independent researcher. Check
# retained syntax, pinned primary citation forms and explicit version limits;
# do not repeat an expensive Blender render or silently claim 4.2 execution.
blender = (HERE / "blender-api-research.md").read_text()
blocks = re.findall(r"```python\n(.*?)```", blender, re.S)
assert len(blocks) == 3
for block in blocks:
    ast.parse(block)
definitions = dict(re.findall(r"^\[([^]]+)\]:\s+(\S+)", blender, re.M))
assert len(definitions) == 24
for key in re.findall(r"\[[^\]\n]+\]\[([^\]\n]+)\]", blender):
    assert key in definitions, key
pinned = [url for url in definitions.values() if "github.com/blender/blender/blob/" in url]
assert len(pinned) == 17 and all("/blob/" + PIN + "/" in url for url in pinned)
assert "not** a claim that Blender 4.2 was executed" in blender

# Strict links for new content only. The old ledger's prior reports/ignored
# reference paths remain historical/local-only, never a decisive dependency.
tracked = set(git("ls-files", "-z").split("\0"))
expected_paths = {LEDGER.relative_to(ROOT).as_posix()} | {p.relative_to(ROOT).as_posix() for p in HERE.rglob("*") if p.is_file()}
expected_paths.add(PREFIX + "/verification.json")
new_ledger = LEDGER.read_text()
new_ledger = new_ledger.split("Task 1 checkpoint,", 1)[0] + new_ledger[new_ledger.index("## Task 3 — repair-gate integration checkpoint"):]
texts = [(p, p.read_text()) for p in sorted(HERE.rglob("*.md"))] + [(LEDGER, new_ledger)]
links = []
external_urls = set()


def slug(text):
    text = re.sub(r"[\[\]`*]", "", text.strip()).lower()
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


for path, text in texts:
    references = dict(re.findall(r"^\[([^]]+)\]:\s+(\S+)", text, re.M))
    destinations = re.findall(r"(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)", text)
    destinations += list(references.values())
    for key in re.findall(r"\[[^\]\n]+\]\[([^\]\n]+)\]", text):
        assert key in references, (path, key)
    for destination in destinations:
        destination = destination.strip("<>")
        if destination.startswith(("https://", "http://")):
            external_urls.add(destination)
            continue
        split = urlsplit(destination)
        target = (path.parent / unquote(split.path)).resolve() if split.path else path.resolve()
        report_will_be_created = args.write_report and target == HERE / "verification.json" and not split.fragment
        assert (target.is_file() or report_will_be_created) and target.is_relative_to(ROOT), (path, destination)
        relative = target.relative_to(ROOT).as_posix()
        assert relative in tracked or relative in expected_paths, (path, "unretained local-only dependency", destination)
        if split.fragment:
            fragment = split.fragment
            line_range = re.fullmatch(r"L(\d+)(?:-L?(\d+))?", fragment)
            if line_range:
                count = len(target.read_text().splitlines())
                assert 1 <= int(line_range.group(1)) <= int(line_range.group(2) or line_range.group(1)) <= count, (target, fragment)
            else:
                headings = {slug(m.group(1)) for m in re.finditer(r"^#+\s+(.+)$", target.read_text(), re.M)}
                assert fragment in headings, (target, fragment, sorted(headings))
        links.append({"from": path.relative_to(ROOT).as_posix(), "to": destination})

for path in HERE.rglob("*.json"):
    if path.name != "verification.json":
        json.loads(path.read_text())
for path in HERE.glob("*.py"):
    ast.parse(path.read_text())
all_files = sorted(p for p in HERE.rglob("*") if p.is_file() and p.name != "verification.json")
assert sum(p.stat().st_size for p in all_files) < retention["limits"]["max_total_bytes"]
assert all(p.suffix in {".md", ".json", ".py", ".c", ".asm", ".txt", ".log"} for p in all_files)
if args.require_staged:
    staged = set(git("diff", "--cached", "--name-only").splitlines())
    assert staged == expected_paths, {"missing": sorted(expected_paths - staged), "extra": sorted(staged - expected_paths)}

result = {"status": "REPAIR_GATE_CHECKPOINT_VERIFIED; TASK3_AND_NATIVE_PARITY_PARTIAL", "base_head": BASE, "native_runtime_observations": False, "fresh_export_commands_rerun": False, "blender_probes_rerun": False, "checks": {"retained_hashes_and_bounds": True, "source_excerpt_identity_when_available": True, "local_originals_checked": local_originals_checked, "all_new_local_links_resolve_to_retained_or_tracked_targets": True, "local_link_count": len(links), "json_and_python_syntax": True, "blender_primary_definitions": 24, "blender_pinned_source_urls": 17, "blender_probe_blocks_parse": 3, "fresh_consumer_functions": 11, "fresh_consumer_fail_prefixes": 0, "fresh_consumer_warning_occurrences": 313, "no_function_not_repaired": "008257cc", "historical_first_attempt_exits": [1, 1], "selected_geometry_acquisition_exits": [item["exit_code"] for item in retention["selected_geometry_acquisitions"]], "assembly_instruction_operand_anchor_count": len(anchors), "research_only_scope": True, "default_live_worktree_scope_check": False, "staging_scope_is_opt_in": True, "exact_staged_path_set": args.require_staged}, "original_export_outcomes": logs, "assembly_anchors": anchors, "new_local_links": links, "external_primary_urls_syntax_checked_not_refetched": sorted(external_urls), "files": [{"path": p.relative_to(HERE).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p.read_bytes())} for p in all_files], "checkpoint_ledger_sha256": CHECKPOINT_LEDGER_SHA256, "checkpoint_ledger_hash_note": "historical initial Task 3 checkpoint; current shared ledger is mutable and is not a live verification input", "open_gates": ["effective final culling/normalization/shaders", "effect material/Power arithmetic", "texture/sampler/render-target/display transfer", "alpha-mode1 history and stale texture binding", "dynamic map/environment/default/variable branches", "special/encrypted/singular origin/normal paths", "derived-only noncommuting globalframe extension", "Blender4.2/5.2 execution coverage", "all native runtime/visual parity"]}
payload = json.dumps(result, indent=2) + "\n"
assert sum(p.stat().st_size for p in all_files) + len(payload.encode()) <= retention["limits"]["max_total_bytes"]
assert len(payload.encode()) <= retention["limits"]["max_single_bytes"]
if args.write_report:
    (HERE / "verification.json").write_text(payload)
else:
    recorded = json.loads((HERE / "verification.json").read_text())
    assert recorded["files"] == result["files"], "Recorded authored/artifact hashes are stale; verify and refresh deliberately"
    assert recorded["assembly_anchors"] == result["assembly_anchors"]
print("TASK3_EVIDENCE_OK retained=%d anchors=%d links=%d consumer_exports=11 warnings=313 staged=%s native_runtime=none" % (len(files), len(anchors), len(links), args.require_staged))
