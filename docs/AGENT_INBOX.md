# GitHub-native agent inbox (experimental)

This is an **optional discovery and notification layer**, not a replacement for
`docs/COORDINATION.md` or the reviewed `docs/sessions/` handoffs. GitHub PR
labels make pending transfers searchable. Event handlers can react to GitHub
activity when separately configured. No human or agent receives new permission
from a PR label, marker or notification.

## Opt a PR into the inbox

Put **exactly one** marker in the **PR description** (not in a comment):

```markdown
<!-- ai-context-next: work -->
```

Change `work` to `codex`, `chatgpt`, or `blocked` as the documented
receiving owner changes. Update the session journal *first*, publish its branch
revision, then edit the PR description to identify the next agent. The marker
is a **routing hint**, not a declaration that work was accepted or finished.

After the workflow is merged into the repository's **default branch**, the
opt-in [handoff inbox Action](../.github/workflows/agent-handoff-inbox.yml)
responds to same-repository PR opened, reopened, description-edited, pushed
and closed events. It maintains **one** of these labels on opted-in PRs:

| Queue label | Meaning |
| --- | --- |
| `ai-next:work` | A published handoff awaits a Work receiver |
| `ai-next:codex` | A published handoff awaits a Codex receiver |
| `ai-next:chatgpt` | A published handoff awaits ChatGPT review |
| `ai-next:blocked` | A published handoff names an unblocker |
| `ai-next:done` | GitHub confirms the PR was merged |
| `ai-next:closed` | GitHub confirms the PR closed without merging |

Labels are lazily created with their descriptions by the Action, and only its
own six labels are reconciled. A PR lacking both a directive and prior queue
labels is **not touched**. If the directive is removed from an opted-in open PR,
the managed label is removed. Multiple recognized directives on an **open** PR fail closed
(the workflow warns and leaves labels unchanged). Terminal merged/closed states
still take precedence, even for an ambiguous marker. Fork PRs are not
automatically labeled.

**Search your inbox:** GitHub Issues search indexes PRs too. For example:

- [Work inbox](https://github.com/yoliverasPozo/AI_CONTEXT/pulls?q=is%3Aopen+label%3Aai-next%3Awork)
- [Codex inbox](https://github.com/yoliverasPozo/AI_CONTEXT/pulls?q=is%3Aopen+label%3Aai-next%3Acodex)
- [ChatGPT inbox](https://github.com/yoliverasPozo/AI_CONTEXT/pulls?q=is%3Aopen+label%3Aai-next%3Achatgpt)
- [Blocked inbox](https://github.com/yoliverasPozo/AI_CONTEXT/pulls?q=is%3Aopen+label%3Aai-next%3Ablocked)

Those URLs are specific to this reference repository; other adopters use their
own repository search. Always open the linked handoff and inspect the actual
branch/commit, tests, acknowledgment and user authorization before acting.

## Connect event-driven consumers

The queue **publishes GitHub activity**. It does **not** start a Chat, Work or
Codex session by itself.

**ChatGPT Work:** When available on the user's account/workspace, create an
*event-triggered Work task* for GitHub PR activity in the authorized repository.
Give the task a condition to act only on PRs assigned to its intended role
(e.g. label `ai-next:work`). Its prompt should fetch the latest PR, read
`AGENTS.md`, `docs/AI_CONTEXT.md`, `docs/COORDINATION.md` and the specific
session journal; verify status, permissions and SHA; acknowledge *on the
branch*; perform only authorized scope; push evidence; update the PR marker
for the next role. Keep approval gates for merges, deployments and production.
Because available event types and event delivery can vary, verify a genuine
PR-label/edited/merged event is delivered before relying on the subscription.

**Codex:** Enable *automatic GitHub pull request code review* for the
repository in Codex settings, or use an explicit `@codex review` in a PR
comment. These are supported review triggers; they do **not** promise a
general-purpose Codex implementation handoff. For task-specific execution,
a separately secured `openai/codex-action@v1` workflow can handle selected
GitHub events, using an **API key in a GitHub Actions secret** and the
narrowest sandbox/permissions. No API key or automatic code-writing job is
installed by this reference action.

**ChatGPT (regular conversation):** This existing chat does not automatically
resume when a GitHub PR changes. A recurring conditional reminder can check
`ai-next:chatgpt` and newly merged/closed PRs and send a notification; it
does not reconstruct or awaken this chat by webhook. A Work event-triggered
review task is another supported option when available. Either receiver must
read the journal and independently verify evidence rather than treating a
notification as acceptance.

## Operating rules

1. Write and publish the source-of-truth handoff journal, including allowed
   actions, next owner, intended outcome, and the tested/inspected revision.
2. Update the PR body marker for the next owner. GitHub's Action reconciles
   the `ai-next:*` label for same-repository PRs on supported events.
3. A recipient opens its queue item, checks that the journal matches current
   Git state, and publishes a separate receiving acknowledgment before work.
4. At completion, the current owner publishes evidence and changes the marker
   to the next role. Closing/merging the PR moves the queue into `closed` or
   `done` automatically. **Do not merge without user authorization.**

Prevent cycles: when a Work-triggered task updates a PR, its next-role marker
must **not** be `work` unless a new Work task is genuinely needed. Consumers
must deduplicate events by repository + PR number + head SHA + target role,
and recheck GitHub state before acting. Transitions are advisory, not locks:
humans resolve conflicting work or ownership. Webhook activity is not evidence
that the downstream agent acted; only the receiver's published acknowledgment is.

## Security and limitations

The routing workflow runs only the trusted, default-branch GitHub Action and
never checks out PR code or executes PR-body text. It uses a narrow literal
marker and a scoped repository token to edit **labels only**; no external
webhook secret, service or API key is needed for the queue itself. It is
intentionally opt-in and limited to same-repository PRs.

GitHub event-triggered Tasks and Codex auto-review each require separate
account-level or repository-level configuration. This repo cannot silently
configure those subscriptions on behalf of all participants. Do not publish
private chat URLs/IDs, tokens, credentials, patient/customer data or sensitive
logs in PRs, handoffs, labels or event summaries. Review agent-output actions
and keep high-impact operations behind explicit approval. This design remains
experimental until a live event-triggered delivery and no-loop test passes.
