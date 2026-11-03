"""Source-only one-item writer. Default invocation never enables a mutation."""
import argparse
import json
from pathlib import Path
import sys
import time

from .planner import PlanError
from .writer import (WriterError, require, prepare, check_proposal, validate_approval,
                     apply, recover, rollback_proposal)
from .writer_github import Backend, validate_config
from .writer_journal import Journal, JournalError


def load(path):
    path=Path(path)
    require(path.stat().st_size<=8*1024*1024,"input exceeds 8 MiB")
    return json.loads(path.read_text(encoding="utf-8"))


def scope(config, before):
    require(config["project"]=={k:before["project"][k] for k in config["project"]}
            and config["target"]=={k:before["target"][k] for k in config["target"]}, "config/proposal scope mismatch")


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest="command",required=True)
    for name in ("prepare","apply","recover","rollback-assess"):
        command=commands.add_parser(name)
        command.add_argument("--config",required=True)
        command.add_argument("--directory",required=True,help="private local operation directory; never copy/reuse")
        if name=="prepare":
            command.add_argument("--snapshot",help="offline complete snapshot instead of live reads")
            command.add_argument("--operation",required=True)
            command.add_argument("--ttl",type=int,default=900)
        if name=="apply":
            command.add_argument("--execute",action="store_true")
            command.add_argument("--approval",help="separately owner-approved exact digest/scope/expiry JSON")
    args=parser.parse_args(argv)
    backend=None
    try:
        config=validate_config(load(args.config))
        now=int(time.time())
        if args.command=="prepare":
            require(0<args.ttl<=3600,"TTL must be 1..3600 seconds")
            if args.snapshot:
                source=load(args.snapshot)
            else:
                backend=Backend(config)  # Never armed for prepare/recovery/rollback.
                source=backend.read()
            proposal=prepare(source,args.operation,now,now+args.ttl)
            scope(config,proposal["before"])
            Journal.create(args.directory,proposal)
            result={"status":"prepared_unapproved","proposal_sha256":proposal["sha256"],
                    "operation_id":proposal["operation_id"],"expires_at":proposal["expires_at"],
                    "existing_items":len(proposal["before"]["items"]),
                    "archived_items":sum(i["archived"] for i in proposal["before"]["items"])}
        else:
            journal=Journal.open(args.directory)
            proposal=journal.events()[0]["data"]["proposal"]
            before=check_proposal(proposal)
            scope(config,before)
            if args.command=="apply":
                require(config["enabled"] is True and args.execute and args.approval,
                        "writer disabled; explicit enablement, --execute and owner approval are required")
                approval=load(args.approval)
                validate_approval(proposal,approval,now,config["enabled"],args.execute)
                backend=Backend(config,armed=True)
                result=apply(proposal,backend,journal,enabled=True,execute=True,approval=approval,now=now)
            elif args.command=="recover":
                backend=Backend(config)
                result=recover(journal,backend)
            else:
                backend=Backend(config)
                result=rollback_proposal(journal,backend.read())
        if backend is not None: result=dict(result,api_usage=backend.metrics)
        print(json.dumps(result,sort_keys=True))
        return 0 if result.get("status") in ("prepared_unapproved","already_present","verified_present") or args.command=="rollback-assess" else 3
    except (WriterError,JournalError,PlanError) as error:
        print(str(error),file=sys.stderr)
        return 2
    except (OSError,ValueError,KeyError,TypeError):
        print("local input/receipt unavailable or malformed; no automatic retry; inspect the operation journal",file=sys.stderr)
        return 2


if __name__=="__main__":
    sys.exit(main())
