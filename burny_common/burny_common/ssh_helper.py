from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from typing import Any

import click
import paramiko
from paramiko import SSHClient


def load_pkey(pkey: str) -> paramiko.PKey | None:
    """Load an RSA private key from a string. Return None when empty to allow password auth."""
    if not pkey or not pkey.strip():
        return None
    return paramiko.RSAKey.from_private_key(StringIO(pkey))


@contextmanager
def connect_ssh(
    host: str,
    port: int = 22,
    username: str = "",
    password: str = "",
    pkey: str = "",
) -> Iterator[SSHClient]:
    """Connect to an SSH server and yield a connected client."""
    with SSHClient() as client:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=host,
            port=port,
            username=username,
            password=password,
            pkey=load_pkey(pkey),
        )
        yield client


def resolve_target_path(client: SSHClient, target_path: str) -> Path:
    """Resolve a target path on the server. Absolute paths are returned directly, relative via pwd."""
    if target_path.startswith("/"):
        return Path(target_path)
    # If target path doesn't start with "/" it means it's a relative path
    _stdin, stdout, _stderr = client.exec_command("pwd")
    return Path(stdout.readline().strip()) / Path(target_path)


def ensure_remote_dir(client: SSHClient, target_folder_path: Path) -> None:
    """Ensure a remote directory exists via mkdir -p."""
    client.exec_command(f"mkdir -p {target_folder_path}")


def ssh_click_options(func: Callable[..., Any]) -> Callable[..., Any]:
    """Add common SSH click options (host/port/username/password/pkey)."""
    # Apply in reverse so --help order stays host, port, username, password, pkey.
    func = click.option("--pkey", default="", help="private key")(func)
    func = click.option("--password", default="", help="user password")(func)
    func = click.option("--username", default="", help="user name")(func)
    func = click.option("--port", default=22, help="port")(func)
    func = click.option("--host", default="", help="host address")(func)
    return func
