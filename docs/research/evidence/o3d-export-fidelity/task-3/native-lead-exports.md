# Lead-authorized Ghidra exports — 2026-11-11 (Asia/Hong_Kong)

## Authorization and scope

Both research workers encountered a real sandbox denial before project open: launcher startup tried to write `/home/mizuki/.config/ghidra/ghidra_12.1.4_PUBLIC/java_home.save`. They correctly did not bypass it. Lead reproduced the denial with the seed command below (exit1); its log was subsequently overwritten by the exact approved retry, but both original worker logs retain the denial.

Lead asked the user: “Ghidra cannot start read-only analysis because its launcher tries to save the selected JDK under ~/.config/ghidra/. May I request approval to retry the analysis with access for that startup cache write? The supplied executable and project will remain read-only.” User selected **Allow startup cache (Recommended)**. The exact seed command was retried with approved wider access. The user subsequently changed runtime policy to danger-full-access with prompts disabled; no further escalation was requested. No installation, project annotation/reanalysis/save, private-copy repair, OMSI launch, Wine-prefix or graphics change occurred.

## Seed command

Working directory: isolated `fix/o3d-export-fidelity` worktree. Literal shell command:

```sh
set -euo pipefail
scratch="$PWD/.superpowers/sdd/2026-11-10-o3d-export-fidelity"
mkdir -p "$scratch/native-authorized-seed"
flock "$scratch/native-export.lock" env JAVA_HOME=/home/mizuki/Downloads/jdk-27 PATH="/home/mizuki/Downloads/jdk-27/bin:$PATH" /mnt/the_dick_disk/ghidra_12.1.4_PUBLIC/support/analyzeHeadless /mnt/Random/users/user/Documents/Ghidra/OMSI OMSI/1 -process Omsi.exe -readOnly -noanalysis -scriptPath "$PWD/docs/research/evidence/omsi-bones" -postScript TraceBoneRuntime.java "$scratch/native-authorized-seed" 0056c7b4 0056af88 005efb98 > "$scratch/native-authorized-seed.log" 2>&1
printf 'Read-only seed completed; log: %s\n' "$scratch/native-authorized-seed.log"
```

Managed job `bash-9ec91a6bf7fa4b65`, collected **exit0**. Log `native-authorized-seed.log` explicitly reports JDK27, read-only `/1/Omsi.exe` open, embedded hash `c7765877620816dd4de4cceb21dce1996c8789c89ee550c1fb58440ee689a33e` and three exported seed functions. No Ghidra index failure occurred.

## Identified-consumer command

```sh
set -euo pipefail
scratch="$PWD/.superpowers/sdd/2026-11-10-o3d-export-fidelity"
mkdir -p "$scratch/native-authorized-consumers"
flock "$scratch/native-export.lock" env JAVA_HOME=/home/mizuki/Downloads/jdk-27 PATH="/home/mizuki/Downloads/jdk-27/bin:$PATH" /mnt/the_dick_disk/ghidra_12.1.4_PUBLIC/support/analyzeHeadless /mnt/Random/users/user/Documents/Ghidra/OMSI OMSI/1 -process Omsi.exe -readOnly -noanalysis -scriptPath "$PWD/docs/research/evidence/omsi-bones" -postScript TraceBoneRuntime.java "$scratch/native-authorized-consumers" 007c5a4c 007fd9b0 007fbee0 005fc664 005ef470 007c73d4 007c315c 008257cc 00800d80 00800d10 007fc878 005fdf40 > "$scratch/native-authorized-consumers.log" 2>&1
printf 'Read-only consumers completed; log: %s\n' "$scratch/native-authorized-consumers.log"
```

Managed job `bash-38b6fa2053184768`, collected **exit0**. `native-authorized-consumers.log` again verifies read-only program open and matching embedded hash. Eleven functions exported. `008257cc` returned **NO FUNCTION** from original metadata; this was not repaired or reanalyzed. Existing bounded original-PE objdump evidence remains the source for that site. A targeted `^FAIL` scan over all emitted `.c` files found none. Decompilations DO contain many nonreturn/unreachable-block warnings; use assembly to corroborate every decisive path and retain those limitations. JDK emits existing reflection/Unsafe warnings; no tool upgrade or new flags were introduced to hide them.

## Integration guidance

These are fresh exports from the verified supplied database, superseding only the environment-availability status, not rewriting workers' historically accurate failed attempts. Selectively retain bounded raw evidence/logs/provenance required by decisions; do not stage the entire scratch workspace, duplicated history, or reference source. Both native reports remain partial static consumer contracts. Effective target cull/normalize state, effect payload/shader arithmetic, color-space state, special/encrypted branches and all actual native rendering remain open. API/math/authoring-policy fixes may proceed where concretely supported; no native visual parity claim.
