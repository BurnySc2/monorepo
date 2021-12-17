import sys
from io import StringIO

import click
import paramiko  # type: ignore
from click.testing import CliRunner
from paramiko import SSHClient


@click.command()
@click.option('--host', default='', help='host address')
@click.option('--port', default=22, help='port')
@click.option('--username', default='', help='user name')
@click.option('--password', default='', help='user password')
@click.option('--pkey', default='', help='private key')
@click.option('--command', default='ls -la', help='command to execute')
def run_command_on_server(host: str, port: int, username: str, password: str, pkey: str, command: str):
    client: SSHClient
    with SSHClient() as client:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        pkey_loaded = paramiko.RSAKey.from_private_key(StringIO(pkey))
        client.connect(hostname=host, port=port, username=username, password=password, pkey=pkey_loaded)
        _stdin, stdout, _stderr = client.exec_command(f'{command}')
        lines = stdout.readlines()
        for line in lines:
            print(line)
    sys.exit(0)


def main():
    runner = CliRunner()
    ip = 'some.url'
    username = 'some_name'
    key = 'my ssh key'
    result = runner.invoke(
        run_command_on_server, [
            f'--host={ip}',
            f'--username={username}',
            f'--pkey={key}',
            '--command=ls -lah',
        ]
    )
    for line in result.output.splitlines():
        print(line)
    if result.exit_code != 0:
        print(result.exception)
        print(result.exit_code)


if __name__ == '__main__':
    main()
