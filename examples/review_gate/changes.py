"""Verify the immutable diff before classifying a PR Lens skip."""

import re

MAX_CHANGED_FILES = 100
MODES = {("blob", "100644"), ("blob", "100755"), ("blob", "120000"),
         ("commit", "160000"), ("tree", "040000")}
ORDINARY = re.compile(r"(?:CHANGELOG\.md|docs/release-notes/v[0-9]+\.[0-9]+\.[0-9]+\.md)\Z")


def need(condition):
    if not condition:
        raise ValueError("invalid changed-file evidence")


def oid(value):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{40}", value) is not None


def path(value):
    return isinstance(value, str) and all(
        re.fullmatch(r"[A-Za-z0-9._-]+", part) and part not in (".", "..")
        and not part.endswith(".")
        for part in value.split("/")
    )


def tree_entries(tree, expected):
    need(oid(expected) and tree["sha"] == expected and tree["truncated"] is False)
    need(type(tree["tree"]) is list)
    entries, seen = {}, set()
    for entry in tree["tree"]:
        name, kind, mode, blob = (entry[key] for key in ("path", "type", "mode", "sha"))
        need(path(name) and name.lower() not in seen and (kind, mode) in MODES and oid(blob))
        seen.add(name.lower())
        if kind != "tree":
            entries[name] = (kind, mode, blob)
    return entries


def verified_changes(bundle, scope, changed_files):
    """Require agreement between the PR list and both immutable Git trees."""
    base = bundle["comparison"]["merge_base_commit"]
    head = bundle["head_commit"]
    need(bundle["comparison"]["base_commit"]["sha"] == scope["base_tip"]
         and oid(base["sha"]) and head["sha"] == scope["head"])
    before = tree_entries(bundle["base_tree"], base["commit"]["tree"]["sha"])
    after = tree_entries(bundle["head_tree"], head["tree"]["sha"])
    changed = {name for name in before.keys() | after.keys() if before.get(name) != after.get(name)}
    files = bundle["files"]
    need(type(files) is list and type(changed_files) is int
         and 0 < changed_files <= MAX_CHANGED_FILES and len(files) == changed_files)
    reported = set()
    for item in files:
        name, status = item["filename"], item["status"]
        previous = item.get("previous_filename")
        need(path(name) and name not in reported)
        old, new = before.get(name), after.get(name)
        if status == "renamed":
            need(path(previous) and previous != name and previous not in reported
                 and previous in before and previous not in after and old is None and new is not None)
            reported.add(previous)
        else:
            need(previous is None and (
                (status == "added" and old is None and new is not None)
                or (status == "removed" and old is not None and new is None)
                or (status in ("modified", "changed") and old is not None and new is not None and old != new)
            ))
        need(item["sha"] == (new or old)[2])
        reported.add(name)
    need(reported == changed)
    entries = [(name, before.get(name), after.get(name)) for name in sorted(changed)]
    if any(not name.endswith(".md") or any(entry and entry[:2] != ("blob", "100644")
                                           for entry in (old, new))
           for name, old, new in entries):
        category = "executable_or_mixed"
    elif all(ORDINARY.fullmatch(name) for name, _, _ in entries):
        category = "ordinary_documentation"
    else:
        category = "sensitive_documentation"
    return category, base["sha"], entries
