# Baseline failure diagnosis

Run on 2026-10-11 with Python 3.12.6 and pytest 9.1.1. Repository and user paths are replaced with `<repo>` and `<python>`; no exception text was otherwise changed.

## 1. Two-process review test

Command:

```powershell
python -m pytest tests/test_review_process.py::test_two_process_approval_then_unavailable_reviewer -vv --tb=long --basetemp .test-tmp/baseline-review-two
```

Result: **1 failed in 3.54 seconds**.

```text
BrokenPipeError: [WinError 109] The pipe has been ended

During handling of the above exception, another exception occurred:

tests/test_review_process.py:48
    args=(receive.recv_bytes(), participant_token, reviewer_token, broker_origin,
          broker_socket, 'saved-family'))

<python>/Lib/multiprocessing/connection.py:216 in recv_bytes
    buf = self._recv_bytes(maxlength)
<python>/Lib/multiprocessing/connection.py:337 in _recv_bytes
    raise EOFError
EOFError

Captured child stderr:
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "<python>/Lib/multiprocessing/spawn.py", line 122, in spawn_main
```

Diagnosis: **environment/Windows spawned-process boundary**. The child exits inside the standard-library spawn bootstrap before `_reviewer` sends its public key. This environment also rejects loopback socket access with WinError 10013. The parent then observes a closed pipe. No core CallGate function runs before the failure.

Proposed resolution: rerun outside the sandbox. If it also fails there, change only the test/demo launcher so each spawned child binds its own socket after startup and reports its port and public key through the pipe; do not pass a pre-bound Windows socket through `spawn`.

## 2. Three-process routing test

Command:

```powershell
python -m pytest tests/test_review_process.py::test_three_process_routing_switch_and_cross_contact_isolation -vv --tb=long --basetemp .test-tmp/baseline-review-three
```

Result: **1 failed in 3.51 seconds**.

```text
BrokenPipeError: [WinError 109] The pipe has been ended

During handling of the above exception, another exception occurred:

tests/test_review_process.py:120
    public_bytes=receive.recv_bytes()))

<python>/Lib/multiprocessing/connection.py:216 in recv_bytes
    buf = self._recv_bytes(maxlength)
<python>/Lib/multiprocessing/connection.py:337 in _recv_bytes
    raise EOFError
EOFError

Captured child stderr:
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "<python>/Lib/multiprocessing/spawn.py", line 122, in spawn_main
```

Diagnosis and proposed resolution: the same spawned-process/socket environment failure as test 1. The failure occurs before routing or contact-isolation logic executes.

## 3. Frozen evaluation-v2 manifest

Command:

```powershell
python -m pytest tests/test_v2_inputs.py::test_input_schema_and_manifest -vv --tb=long --basetemp .test-tmp/baseline-v2-manifest
```

Result: **1 failed in 1.50 seconds**.

```text
tests/test_v2_inputs.py:21 in test_input_schema_and_manifest
    verifier().main()
evaluation_v2/verify_inputs.py:59 in main
    raise ValueError(f'manifest mismatch: {name}')
ValueError: manifest mismatch: blind/scenarios.jsonl
```

Diagnosis: **checkout line-ending configuration, not a frozen-data defect**. The manifest hash and the bytes stored in `HEAD` are both `c6278c926c623e1d2da003d708087d94d1ee4091b55a2bdb1e3c2302535a7ad6`. The current Windows working-tree file hashes to `89b42fe7019933d206b94a98563b8ce870fcc0c254c223ca397f43b1eb00d411`. This checkout has `core.autocrlf=true`; `evaluation_v1/**` has `text: unset`, while `evaluation_v2/**` is unspecified.

No frozen file or manifest was changed.

## Owner-side clean-clone diagnosis

Run from the parent directory of the repository:

```powershell
git clone -c core.autocrlf=false <LOCAL_ORIGIN_PATH> callgate-hash-check
Set-Location callgate-hash-check
py -3.12 -m evaluation_v2.verify_inputs

$path = "evaluation_v2/blind/scenarios.jsonl"
Get-FileHash -Algorithm SHA256 $path
git check-attr text -- evaluation_v1/** evaluation_v2/**
git log --oneline -- $path evaluation_v2/manifest.sha256.json
```

For an exact `git show` byte comparison without PowerShell text conversion, use Python in that clone:

```powershell
py -3.12 -c "import hashlib,pathlib,subprocess; p='evaluation_v2/blind/scenarios.jsonl'; print(hashlib.sha256(subprocess.check_output(['git','show','HEAD:'+p])).hexdigest()); print(hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest())"
```

- If the clean-clone verifier passes and `HEAD` equals the worktree, keep the frozen data unchanged and add `evaluation_v2/** -text` to `.gitattributes` in a separate approved commit.
- If `HEAD` matches the manifest but the worktree differs, this is line-ending conversion; use the same `.gitattributes` remedy and recreate the checkout. Do not edit the manifest.
- If the `HEAD` blob itself differs from the manifest, stop and inspect `git log -- <path>`; treat it as a possible frozen-data/history inconsistency and do not regenerate either side.

