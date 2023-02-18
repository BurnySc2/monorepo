import subprocess
import sys
from io import StringIO
from pathlib import Path
from typing import Optional, Set

import click
import paramiko  # type: ignore
from click.testing import CliRunner
from paramiko import SSHClient
from paramiko.sftp_client import SFTPClient  # type: ignore

from burny_common.copy_file_to_server import copy_file_to_server_helper, generate_path


def copy_folder_to_server_helper(
    client: SSHClient,
    sftp: SFTPClient,
    path_source_root_folder: Path,
    path_target_root_folder: Path,
    file_or_folder: Path,
    allowed_files: Optional[Set] = None,
):
    source_path_relative_to_root = file_or_folder.relative_to(path_source_root_folder)
    if file_or_folder.is_file():
        if allowed_files is not None and file_or_folder.absolute() not in allowed_files:
            # print(f"Ignoring file/folder {file_or_folder}")
            return
        # print(f"Copying file {file_or_folder}")
        path_target = path_target_root_folder / source_path_relative_to_root
        copy_file_to_server_helper(client, sftp, file_or_folder, path_target, create_target_folder=True)
    else:
        for file_or_folder2 in file_or_folder.iterdir():
            # Recursively copy folders
            copy_folder_to_server_helper(
                client,
                sftp,
                path_source_root_folder,
                path_target_root_folder,
                file_or_folder2,
                allowed_files=allowed_files,
            )


@click.command()
@click.option('--host', default='', help='host address')
@click.option('--port', default=22, help='port')
@click.option('--username', default='', help='user name')
@click.option('--password', default='', help='user password')
@click.option('--pkey', default='', help='private key')
@click.option('--sourcepath', default='', help='source folder to copy')
@click.option('--targetpath', default='', help='which folder the output should be')
@click.option('--respectgitignore', default=True, help='ignore files that are ignored by .gitignore')
def copy_folder_to_server(
    host: str,
    port: int,
    username: str,
    password: str,
    pkey: str,
    sourcepath: str,
    targetpath: str,
    respectgitignore: bool = True
):
    client: SSHClient
    with SSHClient() as client:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        pkey_loaded = paramiko.RSAKey.from_private_key(StringIO(pkey))
        client.connect(hostname=host, port=port, username=username, password=password, pkey=pkey_loaded)

        path_source_root_folder = Path(sourcepath)
        path_target_root_folder = generate_path(client, targetpath)

        allowed_files: Optional[Set] = None
        if respectgitignore:
            proc = subprocess.Popen(
                ['git', 'ls-files'],
                cwd=path_source_root_folder.absolute(),
                stdout=subprocess.PIPE,
            )
            output = proc.stdout
            if output is not None:
                files = output.read().decode()
                allowed_files = {(path_source_root_folder / Path(file)).absolute() for file in files.splitlines()}

        with client.open_sftp() as sftp:
            assert path_source_root_folder.is_dir()
            copy_folder_to_server_helper(
                client,
                sftp,
                path_source_root_folder,
                path_target_root_folder,
                # Start copying this folder
                path_source_root_folder,
                allowed_files=allowed_files,
            )
    sys.exit(0)


def main():
    runner = CliRunner()
    ip = 'some.url'
    username = 'some_name'
    key = 'my ssh key'
    result = runner.invoke(
        copy_folder_to_server, [
            f'--host={ip}',
            f'--username={username}',
            f'--pkey={key}',
            '--sourcepath=/home/burny/github/python-template',
            '--targetpath=test5',
        ]
    )
    for line in result.output.splitlines():
        print(line)
    if result.exit_code != 0:
        print(result.exception)
        print(result.exit_code)


if __name__ == '__main__':
    main()
