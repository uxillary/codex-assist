"""Minimal CLI demo for context engine."""
from __future__ import annotations
import argparse
from .engine import ContextEngine


def main():
    parser = argparse.ArgumentParser(prog="context-engine")
    sub = parser.add_subparsers(dest="cmd")

    ing = sub.add_parser("ingest")
    ing.add_argument("--user", required=True)
    ing.add_argument("--assistant", required=True)

    comp = sub.add_parser("compose")
    comp.add_argument("--next", required=True)

    sub.add_parser("stats")

    args = parser.parse_args()
    engine = ContextEngine()
    if args.cmd == "ingest":
        engine.update_memory(args.user, args.assistant)
    elif args.cmd == "compose":
        ctx = engine.compose_context(args.next)
        print(ctx)
    elif args.cmd == "stats":
        print(engine.stats())
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
