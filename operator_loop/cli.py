"""The `operator-loop` command and its subcommands."""

import argparse

from operator_loop.config import require_keys


def cmd_run(args: argparse.Namespace) -> None:
    from operator_loop.experiment import run_experiment

    run_experiment()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="operator-loop",
        description="Teach an AI agent your playbook, one approved rule at a time.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run", help="Run the agent on every case and measure executable coverage").set_defaults(func=cmd_run)

    args = parser.parse_args()
    require_keys()
    args.func(args)


if __name__ == "__main__":
    main()
