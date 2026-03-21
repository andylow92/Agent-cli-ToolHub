"""CLI Tools Hub — Main entrypoint and subcommand routing."""

import argparse
import sys

from src import __version__


def main():
    parser = argparse.ArgumentParser(
        prog="ath",
        description="CLI Tools Hub — AI-agent-friendly tools as subcommands.",
    )
    parser.add_argument("--version", action="version", version=f"ath {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available tools")

    # --- weather ---
    weather_parser = subparsers.add_parser("weather", help="Get current weather for a city")
    weather_parser.add_argument("--city", required=True, help="City name (e.g. 'London' or 'London,GB')")
    weather_parser.add_argument(
        "--units",
        choices=["metric", "imperial", "standard"],
        default="metric",
        help="Temperature units (default: metric)",
    )

    # --- search ---
    search_parser = subparsers.add_parser("search", help="AI-powered web search via Perplexity")
    search_parser.add_argument("--query", required=True, help="Search query or question")
    search_parser.add_argument("--max-results", type=int, default=1024, help="Max tokens in response (default: 1024)")
    search_parser.add_argument(
        "--model",
        choices=["sonar", "sonar-pro"],
        default="sonar",
        help="Perplexity model (default: sonar)",
    )
    search_parser.add_argument(
        "--recency",
        choices=["day", "week", "month", "year"],
        default=None,
        help="Filter sources by recency",
    )

    # --- convert ---
    convert_parser = subparsers.add_parser("convert", help="Convert between file formats")
    convert_parser.add_argument("--input", required=True, dest="input_file", help="Input file path")
    convert_parser.add_argument("--to", required=True, dest="to_format", help="Target format (csv, json, xml, html, markdown, text, tsv, pdf, xlsx)")
    convert_parser.add_argument("--output", dest="output_file", default=None, help="Output file path (required for binary formats)")

    # --- verify ---
    verify_parser = subparsers.add_parser("verify", help="Verified inter-agent communication")
    verify_group = verify_parser.add_mutually_exclusive_group(required=True)
    verify_group.add_argument("--send", action="store_true", help="Send a verified message to an agent")
    verify_group.add_argument("--check", action="store_true", help="Verify a response contains the correct request_id")
    verify_parser.add_argument("--to", dest="target_url", help="Target agent URL (required with --send)")
    verify_parser.add_argument("--message", help="Message to send (required with --send)")
    verify_parser.add_argument("--request-id", help="Request ID to verify (required with --check)")
    verify_parser.add_argument("--response", help="Response text to verify (required with --check)")
    verify_parser.add_argument("--timeout", type=int, default=10000, help="Timeout in milliseconds (default: 10000)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "weather":
        from src.weather import run
        run(args)
    elif args.command == "search":
        from src.search import run
        run(args)
    elif args.command == "convert":
        from src.convert import run
        run(args)
    elif args.command == "verify":
        from src.verify import run
        run(args)


if __name__ == "__main__":
    main()
