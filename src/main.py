import argparse
import sys

from .codegen import emit_python
from .gui import run_gui
from .runtime import run_project
from .tester import run_testset
from .validator import load_json_file


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Flowchart Threads")
    parser.add_argument("--run", metavar="PATH", help="Run a JSON project")
    parser.add_argument("--emit", metavar="PATH", help="Emit Python source code")
    parser.add_argument("--test", metavar="PATH", help="Run a test set JSON")
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--max-schedules", type=int, default=None)
    parser.add_argument("--k", type=int, default=None, help="Report progress for <= K steps")

    args = parser.parse_args(argv)

    if args.test and not args.run:
        print("--test requires --run PATH", file=sys.stderr)
        return 2

    if args.run:
        data = load_json_file(args.run)
        if args.emit:
            emit_python(args.emit, data)
            return 0
        if args.test:
            if args.k is not None and not (1 <= args.k <= 20):
                print("--k must be in range 1..20", file=sys.stderr)
                return 2
            testset = load_json_file(args.test)
            max_steps = args.max_steps or 100
            return run_testset(
                data,
                testset,
                max_steps=max_steps,
                max_schedules=args.max_schedules,
                k_limit=args.k,
            )
        run_project(data, max_steps=args.max_steps)
        return 0

    if args.emit and not args.run:
        print("--emit requires --run PATH", file=sys.stderr)
        return 2

    run_gui()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
