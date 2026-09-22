import sys
from pathlib import Path

import click
from click.testing import CliRunner
from paramiko import SSHClient
from paramiko.sftp_client import SFTPClient

from burny_common.ssh_helper import connect_ssh, ensure_remote_dir, resolve_target_path, ssh_click_options


def generate_path(client: SSHClient, target_path: str) -> Path:
    """Backward-compatible shim for resolve_target_path."""
    return resolve_target_path(client, target_path)


def create_target_dir(client: SSHClient, target_folder_path: Path):
    """Backward-compatible shim for ensure_remote_dir."""
    ensure_remote_dir(client, target_folder_path)


def copy_file_to_server_helper(
    client: SSHClient,
    sftp: SFTPClient,
    source_path: Path,
    target_path: Path,
    create_target_folder: bool = True,
):
    if create_target_folder:
        create_target_dir(client, target_path.parent)
    return sftp.put(str(source_path.absolute()), str(target_path.absolute()))


@click.command()
@ssh_click_options
@click.option("--sourcepath", default="", help="source file to copy")
@click.option("--targetpath", default="", help="target path to copy the file to")
@click.option("--createtargetdir", default=True, help="create directory if file doesnt exist")
def copy_file_to_server(
    host: str,
    port: int,
    username: str,
    password: str,
    pkey: str,
    sourcepath: str,
    targetpath: str,
    createtargetdir: bool = True,
):
    with connect_ssh(host, port, username, password, pkey) as client:
        path_source = Path(sourcepath)
        path_target = resolve_target_path(client, target_path=targetpath)

        with client.open_sftp() as sftp:
            assert path_source.is_file()
            print(f"Copying {path_source.absolute()} to {path_target.absolute()}")
            copy_file_to_server_helper(
                client,
                sftp,
                path_source,
                path_target,
                create_target_folder=createtargetdir,
            )
    sys.exit(0)


def main():
    runner = CliRunner()
    ip = "some.url"
    username = "some_name"
    key = "my ssh key"
    result = runner.invoke(
        copy_file_to_server,
        [
            f"--host={ip}",
            f"--username={username}",
            f"--pkey={key}",
            "--sourcepath=copy_file_to_server.py",
            "--targetpath=test2/copy_file_to_server3.py",
        ],
    )
    for line in result.output.splitlines():
        print(line)
    if result.exit_code != 0:
        print(result.exception)
        print(result.exit_code)


if __name__ == "__main__":
    main()
