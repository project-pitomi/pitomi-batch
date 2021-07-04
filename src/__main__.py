import argparse
import asyncio
from .func import fetch, build_webp, classify


def main():
    parser = argparse.ArgumentParser(description="Process some utility jobs.")
    parser.add_argument(
        "function",
        type=str,
        help="fetch | build_webp | classify",
        choices=["fetch", "build_webp", "classify"],
    )
    parser.add_argument(
        "count",
        type=int,
        help="maximum number of items to execute on",
        choices=range(0, 1000),
    )

    args = parser.parse_args()
    func = {
        "fetch": fetch.execute,
        "build_webp": build_webp.execute,
        "classify": classify.execute,
    }[args.function]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(func(args.count))


main()
