# O3D export fidelity: Task 1 evidence

Research-only checkpoint against repository base `23c7ef6396b451fb77f6f7841b17d24e5cc45d37`.

- `identities.json`: bounded executable, reference source, Blender and existing fixture identities; initial Git state and exact Blender version output.
- `fixture-inventory.json`: one isolated, auto-execution-disabled background Blender process per existing `.blend`; no source asset is saved.
- `caller-contracts.json`: direct Python call sites for the four shared export helpers, extracted from current repository Python source (reference checkout excluded).
- `checkpoint-probes.json`: bounded in-memory source/codec/Blender observations; not native rendering evidence.

The executable and original Ghidra project are read-only inputs. No OMSI process is launched, no Ghidra analysis or annotations are changed, and no third-party source is modified. Historical research remains untouched. Hash mismatch with the recorded executable prevents attributing its addresses to another build. Reference source hashes are independent of the root Git commit.

See [current-status ledger](../../2026-11-10-o3d-export-fidelity.md) for interpretation and unresolved gates. A Blender round trip, reference-source comparison, static executable trace, mathematical deduction and authoring choice are distinct evidence classes; none establishes native visual parity.
