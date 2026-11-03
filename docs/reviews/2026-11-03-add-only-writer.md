# Independent review: disabled add-only writer

Date: 2026-11-03. Independent review agent; offline only, no implementation edits.
Scope: new writer policy, journal, fixed transport/reader, CLI, tests, operator
guide, ADR, session and context against base
`d0c9cbf770d12d505b08210c3ed42f9ae0cded4b` and the recorded design.

## Result

Final independent run: **85 tests passed**, using this checkout's
`src/ai_context/__init__.py`. No remaining blockers identified. Relative document
links resolved and `git diff --check` passed. No network or live mutation was
performed by the reviewer; live-read evidence is author-observed, not independently
revalidated here. Review does not authorize merge, pilot, deployment or schedules.

## Findings and resolution

| Priority | Finding | Resolution and regression evidence |
| --- | --- | --- |
| P1 | Approval could expire during a slow preflight | Recheck current time before intent and after fsync; both expiry paths tested, no send |
| P1 | Null/malformed populated repository or milestone could appear complete | Require related node identity and selected payload; null/missing-shape regressions refuse |
| P2 | Repeated recovery could append beyond the journal's readable limit | Prospective capacity check refuses before write, preserving original receipt bytes |
| P2 | Organization config allowed an impossible viewer/owner match | Narrow config to user-owned Projects; explicit rejection test |

Reviewer independently repeated malformed-relation and real 7 MiB receipt-growth
reproductions after the fixes. Additional suggested tests now cover paging drift,
duplicate content/repeated cursors, invalid/mismatched mutation acknowledgment,
expiry during intent fsync, and final receipt failure with reopen/recovery and
no resend. Author also fixed terminal no-op replay and added its regression.

## Reviewed implementation fingerprints

Raw UTF-8 file SHA-256 at final review, before publication; runtime code/tests
were unchanged afterward. Subsequent edits only record review/delivery evidence.

| File | SHA-256 |
| --- | --- |
| `writer.py` | `24a0b3020638bb530b2ca3aac532f80c9e45a9f0565c574347dd33ec5c628acb` |
| `writer_cli.py` | `b6be4fd131990bf65a81944fa3b95e48b82380a33bb123f509f6e74b1f2fe85e` |
| `writer_github.py` | `76849ece8f1f413a1c5790139b6a2ab470f21cbc9c98a2508f04f0f4be2f126c` |
| `writer_journal.py` | `7ed4b15098cad3fc91411df59e6f691cc786343cd3993263b825cc25048543f3` |
| `test_project_writer.py` | `b405c9b5851b6fc0cabae7e1753a6fa8baaecdb5beceef0344d4b51cf0c52def` |
| `test_project_writer_cli.py` | `7ed1a75ea78f86f07956c0c85837f81137ab4d57f3cbb5c22350e37f4db10404` |
| `test_project_writer_github.py` | `172ffc85a89c058ef9792facf461f67937a6c8ac6ea8daea67f07d892942b063` |

Files are under `examples/project_sync/` and `tests/`, respectively. Public
fixtures contain generic identifiers; private portfolio state/pilot records
remain outside this repository. Exact Git revision and natural CI belong in the
draft PR, since a commit cannot embed its own hash.
