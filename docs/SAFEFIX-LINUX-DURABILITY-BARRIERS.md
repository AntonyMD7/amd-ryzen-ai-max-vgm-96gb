# SafeFix Linux durability barriers v0.4

**Canonical foundation:** F-01 SafeFix  
**State:** IN PROGRESS supporting acceptance — not a production or power-loss-atomicity claim.

## Purpose

SafeFix already retained a recovery snapshot and PREPARED journal before mutation, used file `fsync()` before `os.replace()`, classified interrupted state and could recover exact original bytes inside an explicit disposable sandbox.

One important durability gap remained in that reference adapter: a successful file flush plus atomic rename does not itself justify claiming that the containing directory entry is durably recorded across a sudden host/power failure. This tranche adds a bounded Linux directory-sync barrier while preserving a truthful non-production boundary.

## Search before build

SafeFix continues to adopt existing primitives rather than inventing an operating-system transaction engine.

- Python's `os.fsync()` documentation says buffered file objects should be flushed and then fsynced to force associated buffers to disk.
- Python documents successful POSIX rename/replace as atomic at the rename operation boundary.
- OSTree is specifically designed around atomic operating-system deployment transitions and rollback; SafeFix should integrate with that class of native mechanism rather than reproduce it for complete OS trees.
- Nix/NixOS keeps generations and supports rollback; SafeFix should similarly treat native generation/rollback systems as stronger domain-specific recovery primitives where available.

Primary references inspected for this tranche:

- https://docs.python.org/3/library/os.html
- https://ostreedev.github.io/ostree/atomic-upgrades/
- https://nixos.org/manual/nixos/stable/

## v0.4 barrier sequence

For each sandbox atomic write:

```text
write temporary file in target directory
        |
        v
flush Python buffer
        |
        v
fsync(temp file descriptor)
        |
        v
os.replace(temp, target)
        |
        v
Linux only: open containing directory + fsync(directory fd)
```

For newly created recovery-directory components, Linux additionally fsyncs the parent directory after each child directory is created. This narrows the gap where the recovery snapshot or journal file is synced but one of its newly created path components has not been explicitly barriered by this harness.

## Cross-platform truth boundary

Directory-fsync behavior is not treated as a portable Python contract in this reference adapter.

The evidence therefore records an explicit `durability_barrier_profile`:

- `file_fsync_before_replace = true`;
- `atomic_replace_requested = true`;
- Linux with `O_DIRECTORY`: parent-directory fsync barriers are requested;
- other platforms: no parent-directory durability claim;
- `power_loss_atomicity_proven = false` everywhere;
- `filesystem_specific_crash_consistency_proven = false` everywhere;
- `hardware_write_cache_durability_proven = false` everywhere.

A Linux directory-fsync open or sync failure raises `SandboxSafeFixError`; it is not silently converted into a green durability claim.

## Backward recovery compatibility

v0.4 writes new journals as schema `0.4`, but inspection and rollback continue to accept v0.3 transaction journals. A v0.3 journal has no `durability_barrier_profile`, so the field is returned as `null` instead of retrospectively claiming barriers that were not recorded at preparation time.

This preserves recovery capability for already-retained v0.3 sandbox transactions.

## Tests

The added durability tests verify:

1. the evidence profile never claims power-loss/filesystem/hardware durability proof;
2. atomic writes request the parent-directory barrier;
3. each newly created recovery directory entry requests a parent barrier;
4. successful transactions retain the profile for later inspection;
5. v0.3 committed journals remain inspectable and recoverable;
6. injected Linux directory-fsync failure is surfaced as a fail-closed error.

Existing SafeFix lifecycle/interruption/corruption/path/symlink/replay tests remain in force.

## What this improves

This is a stronger **durability-barrier implementation and evidence contract** for the Linux sandbox adapter. It makes the reference implementation more explicit about what is synced and prevents a directory-fsync failure from being silently treated as durable success.

## What it does not prove

This does not prove:

- behavior under an actual power cut;
- filesystem-specific crash consistency for ext4/XFS/Btrfs/ZFS/APFS/NTFS or network filesystems;
- storage-controller or device write-cache persistence;
- true multi-resource atomicity;
- service/process/package/registry/firmware rollback;
- production safety;
- completion of F-01.

Representative non-production crash/power-loss testing and native transaction adapters remain separate completion gates.
