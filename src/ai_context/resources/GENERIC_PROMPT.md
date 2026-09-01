# Generic AI Agent Bootstrap Prompt

Use this when an AI coding tool does not have a dedicated repository instruction file or when you want to bootstrap a new agent into an AI_CONTEXT-enabled project.

```text
This repository uses a shared AI project-context layer.

Before substantial work:

1. Read docs/AI_CONTEXT.md.
2. Read relevant accepted records under docs/decisions/.
3. Read relevant recent handoffs under docs/sessions/ when prior debugging,
   experiments, or unfinished work may affect this task.
4. Inspect the current code, configuration, tests, and Git state before
   trusting documentation blindly.

When sources conflict, prefer current observable repository/runtime truth,
then accepted decision records, then the current context summary, then recent
session handoffs, then remembered conversation context.

After substantial work:

- update docs/AI_CONTEXT.md if the current project state changed;
- create/update a session handoff if another developer or agent would benefit
  from the continuation context;
- create a decision record for durable architectural or design choices;
- preserve meaningful failed approaches that future agents might otherwise
  repeat;
- keep the current-state file concise and remove stale information.

If conversation history is missing, compacted, interrupted, or ambiguous,
recover from the repository rather than guessing or repeating completed work.

Do not store secrets, credentials, private keys, tokens, sensitive personal
information, full raw chat transcripts, or hidden chain-of-thought in shared
context. Record concise engineering conclusions, requirements, tradeoffs,
validation results, failures, and decisions instead.
```
