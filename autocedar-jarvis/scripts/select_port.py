"""Choose an unused loopback port for one Jarvis model-server job."""

from __future__ import annotations

import argparse
import socket
from collections.abc import Iterator, Sequence


DYNAMIC_PORT_MIN = 20_000
DYNAMIC_PORT_MAX = 59_999


def port_is_available(port: int, *, host: str = "127.0.0.1") -> bool:
    """Return whether a TCP listener can bind ``host:port`` right now."""

    if not 1 <= port <= 65_535:
        raise ValueError(f"port must be between 1 and 65535 (found: {port})")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        try:
            listener.bind((host, port))
        except OSError:
            return False
    return True


def _fallback_ports(job_id: int) -> Iterator[int]:
    width = DYNAMIC_PORT_MAX - DYNAMIC_PORT_MIN + 1
    start = DYNAMIC_PORT_MIN + (job_id % width)
    for offset in range(width):
        yield DYNAMIC_PORT_MIN + ((start - DYNAMIC_PORT_MIN + offset) % width)


def select_port(preferred: int, job_id: int, *, host: str = "127.0.0.1") -> int:
    """Use ``preferred`` when free, otherwise choose a job-specific free port."""

    if job_id <= 0:
        raise ValueError(f"job_id must be a positive integer (found: {job_id})")
    if port_is_available(preferred, host=host):
        return preferred
    for candidate in _fallback_ports(job_id):
        if candidate != preferred and port_is_available(candidate, host=host):
            return candidate
    raise RuntimeError(
        f"no free TCP port found between {DYNAMIC_PORT_MIN} and {DYNAMIC_PORT_MAX}",
    )


def main(argv: Sequence[str] = ()) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preferred", type=int, required=True)
    parser.add_argument("--job-id", type=int, required=True)
    args = parser.parse_args(list(argv))
    try:
        selected = select_port(args.preferred, args.job_id)
    except (RuntimeError, ValueError) as exc:
        parser.exit(1, f"Could not select a local model port: {exc}\n")
    print(selected)


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
