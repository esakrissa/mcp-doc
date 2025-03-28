#!/usr/bin/env python3
"""Command-line interface for MCP documentation server."""

import argparse
import json
import os
import signal
import sys
import asyncio
from typing import List, Dict

import yaml

from mcpdoc._version import __version__
from mcpdoc.main import create_server, DocSource
from mcpdoc.splash import SPLASH


class CustomFormatter(
    argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter
):
    # Custom formatter to preserve epilog formatting while showing default values
    pass


EPILOG = """
Examples:
  # Directly specifying documentation files with optional names
  mcpdoc --urls LangGraph:https://esakrissa.github.io/mcpdoc/docs/langgraph.txt
  
  # Using a local file (absolute or relative path)
  mcpdoc --urls MCP:/path/to/mcp.txt --allowed-domains '*'
  
  # Using a YAML config file
  mcpdoc --yaml sample_config.yaml

  # Using a JSON config file
  mcpdoc --json sample_config.json

  # Combining multiple documentation sources
  mcpdoc --yaml sample_config.yaml --json sample_config.json --urls LangGraph:https://esakrissa.github.io/mcpdoc/docs/langgraph.txt

  # Using SSE transport with default host (127.0.0.1) and port (8000)
  mcpdoc --yaml sample_config.yaml --transport sse
  
  # Using SSE transport with custom host and port
  mcpdoc --yaml sample_config.yaml --transport sse --host 0.0.0.0 --port 9000
  
  # Using SSE transport with additional HTTP options
  mcpdoc --yaml sample_config.yaml --follow-redirects --timeout 15 --transport sse --host localhost --port 8080
  
  # Allow fetching from additional domains. The domains hosting the documentation files are always allowed.
  mcpdoc --yaml sample_config.yaml --allowed-domains https://example.com/ https://another-example.com/
  
  # Allow fetching from any domain
  mcpdoc --yaml sample_config.yaml --allowed-domains '*'
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    # Custom formatter to preserve epilog formatting
    parser = argparse.ArgumentParser(
        description="MCP Documentation Server",
        formatter_class=CustomFormatter,
        epilog=EPILOG,
    )

    # Allow combining multiple doc source methods
    parser.add_argument(
        "--yaml", "-y", type=str, help="Path to YAML config file with doc sources"
    )
    parser.add_argument(
        "--json", "-j", type=str, help="Path to JSON config file with doc sources"
    )
    parser.add_argument(
        "--urls",
        "-u",
        type=str,
        nargs="+",
        help="List of documentation file URLs or file paths with optional names (format: 'url_or_path' or 'name:url_or_path')",
    )

    parser.add_argument(
        "--follow-redirects",
        action="store_true",
        help="Whether to follow HTTP redirects",
    )
    parser.add_argument(
        "--allowed-domains",
        type=str,
        nargs="*",
        help="Additional allowed domains to fetch documentation from. Use '*' to allow all domains.",
    )
    parser.add_argument(
        "--timeout", type=float, default=10.0, help="HTTP request timeout in seconds"
    )
    parser.add_argument(
        "--transport",
        type=str,
        default="stdio",
        choices=["stdio", "sse"],
        help="Transport protocol for MCP server",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help=(
            "Log level for the server. Use one on the following: DEBUG, INFO, "
            "WARNING, ERROR."
            " (only used with --transport sse)"
        ),
    )

    # SSE-specific options
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind the server to (only used with --transport sse)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (only used with --transport sse)",
    )

    # Version information
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"mcpdoc {__version__}",
        help="Show version information and exit",
    )

    return parser.parse_args()


def load_config_file(file_path: str, file_format: str) -> List[Dict[str, str]]:
    """Load configuration from a file.

    Args:
        file_path: Path to the config file
        file_format: Format of the config file ("yaml" or "json")

    Returns:
        List of doc source configurations
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            if file_format.lower() == "yaml":
                config = yaml.safe_load(file)
            elif file_format.lower() == "json":
                config = json.load(file)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")

        if not isinstance(config, list):
            raise ValueError("Config file must contain a list of doc sources")

        return config
    except (FileNotFoundError, yaml.YAMLError, json.JSONDecodeError) as e:
        print(f"Error loading config file: {e}", file=sys.stderr)
        sys.exit(1)


def create_doc_sources_from_urls(urls: List[str]) -> List[DocSource]:
    """Create doc sources from a list of URLs or file paths with optional names.

    Args:
        urls: List of documentation file URLs or file paths with optional names
             (format: 'url_or_path' or 'name:url_or_path')

    Returns:
        List of DocSource objects
    """
    doc_sources = []
    for entry in urls:
        if not entry.strip():
            continue
        if ":" in entry and not entry.startswith(("http:", "https:")):
            # Format is name:url
            name, url = entry.split(":", 1)
            doc_sources.append({"name": name, "doc_file": url})
        else:
            # Format is just url
            doc_sources.append({"doc_file": entry})
    return doc_sources


def main() -> None:
    """Main entry point for the CLI."""
    # Custom exception hook to handle asyncio.CancelledError and KeyboardInterrupt gracefully
    original_excepthook = sys.excepthook
    
    def custom_excepthook(exc_type, exc_value, exc_traceback):
        # Suppress KeyboardInterrupt and asyncio.CancelledError
        if exc_type in (KeyboardInterrupt, asyncio.exceptions.CancelledError):
            print("\nShutting down gracefully... Goodbye!")
            return
        # For all other exceptions, use the original excepthook
        return original_excepthook(exc_type, exc_value, exc_traceback)
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        print("\nShutting down gracefully... Goodbye!")
        sys.exit(0)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Replace the default exception hook
    sys.excepthook = custom_excepthook

    # Check if --help or -h is in arguments
    if "--help" in sys.argv or "-h" in sys.argv:
        help_parser = argparse.ArgumentParser(
            prog="mcpdoc",
            description="MCP Documentation Server",
            formatter_class=CustomFormatter,
            epilog=EPILOG,
        )
        # Add version to help parser too
        help_parser.add_argument(
            "--version",
            "-V",
            action="version",
            version=f"mcpdoc {__version__}",
            help="Show version information and exit",
        )
        help_parser.print_help()
        sys.exit(0)

    args = parse_args()

    # Load doc sources based on command-line arguments
    doc_sources: List[DocSource] = []

    # Check if any source options were provided
    if not (args.yaml or args.json or args.urls):
        print(
            "Error: At least one source option (--yaml, --json, or --urls) is required",
            file=sys.stderr,
        )
        sys.exit(1)

    # Merge doc sources from all provided methods
    if args.yaml:
        doc_sources.extend(load_config_file(args.yaml, "yaml"))
    if args.json:
        doc_sources.extend(load_config_file(args.json, "json"))
    if args.urls:
        doc_sources.extend(create_doc_sources_from_urls(args.urls))

    # Only used with SSE transport
    settings = {
        "host": args.host,
        "port": args.port,
        "log_level": "INFO",
    }

    # Create and run the server
    server = create_server(
        doc_sources,
        follow_redirects=args.follow_redirects,
        timeout=args.timeout,
        settings=settings,
        allowed_domains=args.allowed_domains,
    )

    # Print startup banner and configuration info
    if args.transport == "sse":
        print(SPLASH)
        print("Starting MCP Documentation Server...")
        print(f"Version: {__version__}")
        print(f"Launching MCP-DOC server with {len(doc_sources)} doc sources")

    # Pass transport-specific options
    try:
        server.run(transport=args.transport)
    except KeyboardInterrupt:
        print("\nShutting down gracefully... Goodbye!")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
