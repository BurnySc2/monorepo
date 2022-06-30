import os
import signal
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path
from typing import Optional, Set

import portpicker
import psutil
import requests
from loguru import logger

WEBSITE_IP = 'http://localhost'


class Timeout:
    """
    Run something for a maximum limited time
    try:
        with Timeout(seconds=2):
            ...
    except TimeoutError:
        ...
    """

    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type_, value, traceback):
        signal.alarm(0)


def get_pid(name: str) -> Set[int]:
    """ Return a list of PIDs of all processes with the exact given name. """
    process_pids = set()
    for proc in psutil.process_iter():
        if name == proc.name():
            pid = proc.pid
            process_pids.add(pid)
    return process_pids


def remove_leftover_files(files: Set[Path]):
    for file in files:
        if file.is_file():
            os.remove(file)


def find_next_free_port(port: int = 10_000, max_port: int = 65_535, exclude_ports: Optional[Set[int]] = None) -> int:
    if exclude_ports is None:
        exclude_ports = set()

    while port <= max_port:
        if port not in exclude_ports and portpicker.is_port_free(port):
            return port
        port += 1
    raise IOError('No free ports')


# pylint: disable=R1732
def check_if_docker_is_running() -> bool:
    p = subprocess.Popen(['docker', 'ps'], stdout=subprocess.PIPE)
    _return_code = p.wait()
    if not p.stdout:
        return False
    output = p.stdout.read().decode()
    docker_running = output.startswith('CONTAINER ID')
    if docker_running:
        logger.info('Docker running detected')
    return docker_running


def get_website_address(port: int) -> str:
    return f'{WEBSITE_IP}:{port}'


def start_svelte_dev_server(
    port: int,
    newly_created_processes: Set[int],
    frontend_folder_path: Path,
    backend_proxy: str = 'localhost:8000',
):
    currently_running_node_processes = get_pid('node')

    assert portpicker.is_port_free(port), f'Unable to start svelte dev server because port {port} is blocked'
    logger.info(f'Starting frontend on port {port}')
    _ = subprocess.Popen(
        ['npx', 'cross-env', f'BACKEND_SERVER={backend_proxy}', 'svelte-kit', 'dev', '--port', f'{port}'],
        cwd=frontend_folder_path,
        env=os.environ.copy()
    )
    # Give it some time to create dev server and all (3?) node proccesses
    with Timeout(10, 'Took more than 10 seconds'):
        while portpicker.is_port_free(port):
            time.sleep(0.1)
        while 1:
            with suppress(requests.exceptions.ConnectionError):
                result = requests.get(get_website_address(port))
                if result.status_code == 200:
                    break
            time.sleep(0.1)

    new_processes = get_pid('node') - currently_running_node_processes
    logger.info(f'New node processes: {new_processes}')
    newly_created_processes |= new_processes


def start_fastapi_dev_server(
    port: int,
    newly_created_processes: Set[int],
    fastapi_folder_path: Path,
):
    print(str(fastapi_folder_path.absolute()))
    currently_running_uvicorn_processes = get_pid('uvicorn')

    # Why does this return errors even when fastapi server is not running
    # assert is_port_free(port), f"Unable to start fastapi server because port {port} is blocked"

    # Switch environment
    switch_environment_command = ['poetry', 'env', 'use', 'python']
    _show_process_result = subprocess.Popen(
        switch_environment_command,
        cwd=fastapi_folder_path,
        # env=os.environ.copy(),
    ).communicate()

    logger.info(f'Starting backend on port {port}')
    command = ['poetry', 'run', 'uvicorn', 'main:app', '--host', 'localhost', '--port', f'{port}']
    logger.info(f'In work directory "{fastapi_folder_path}" running command: {command}')
    process = subprocess.Popen(
        command,
        cwd=fastapi_folder_path,
        # env=os.environ.copy(),
    )

    # Check if process has ended - that means there was an error
    with suppress(subprocess.TimeoutExpired):
        return_code = process.wait(timeout=1)
        logger.info(return_code)

        logger.info('Show envs')
        command_show_packages = ['poetry', 'env', 'list']
        _show_process_result = subprocess.Popen(
            command_show_packages,
            cwd=fastapi_folder_path,
            # env=os.environ.copy(),
        ).communicate()

        logger.info('List poetry packages')
        command_show_packages = ['poetry', 'show', '-v']
        _show_process_result = subprocess.Popen(
            command_show_packages,
            cwd=fastapi_folder_path,
            # env=os.environ.copy(),
        ).communicate()

        if return_code == 1:
            sys.exit(1)

    # Give it some time to create backend dev server
    with Timeout(10, 'Took more than 10 seconds'):
        while portpicker.is_port_free(port):
            time.sleep(0.1)
        while 1:
            with suppress(requests.exceptions.ConnectionError):
                result = requests.get(get_website_address(port))
                if result.status_code == 200:
                    break
            time.sleep(0.1)

    new_processes: Set[int] = get_pid('uvicorn') - currently_running_uvicorn_processes
    logger.info(f'New uvicorn processes: {new_processes}')
    newly_created_processes |= new_processes


# def check_if_mongodb_is_running(mongo_db_port: int = 27017) -> bool:
#     mongo_db_address = f'mongodb://localhost:{mongo_db_port}'
#     try:
#         with Timeout(seconds=2):
#             _my_client: MongoClient
#             with pymongo.MongoClient(mongo_db_address) as _my_client:
#                 pass
#     except TimeoutError:
#         return False
#     return True
#
#
# # pylint: disable=R1732
# def start_mongodb(mongo_db_port: int = 27017) -> int:
#     # Start mongodb via docker
#     if check_if_mongodb_is_running(mongo_db_port):
#         logger.info(f'MongoDB is already running on port {mongo_db_port}')
#         return mongo_db_port
#     command = [
#         # TODO add volume to save db
#         'docker',
#         'run',
#         '--rm',
#         '-d',
#         '--name',
#         'mongodb_test',
#         '-p',
#         # TODO use mongo_db_port
#         '27017-27019:27017-27019',
#         'mongo:5.0.0',
#     ]
#     logger.info(f"Starting mongoDB with command: {' '.join(command)}")
#     process = subprocess.Popen(command)
#     process.wait()
#     return mongo_db_port


def check_if_postgres_is_running(port: int = 5432) -> bool:
    # If we can connect to port 5432, postgres is already running
    # TODO find better way to figure out if postgress is running
    return not portpicker.is_port_free(port)


# pylint: disable=R1732
def start_postgres(postgres_port: int = 5432) -> int:
    # Start postgres via docker
    if check_if_postgres_is_running(postgres_port):
        logger.info(f'Postgres is already running on port {postgres_port}')
        return postgres_port
    postgres_container_name = 'postgres_test'
    postgres_volume_name = 'postgres_test'
    postgres_username = 'postgres'
    postgres_password = 'changeme'
    postgres_image = 'postgres:9.6.23-alpine3.14'
    # postgres_port = find_next_free_port()
    if check_if_docker_is_running():
        # docker run --rm --name postgres_test -p 5432:5432 --volume postgres_test:/data/postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=changeme postgres:9.6.23-alpine3.14
        command = [
            # TODO add volume to save db, or should that not be active while testing?
            'docker',
            'run',
            '--rm',
            '-d',
            '--name',
            postgres_container_name,
            '-p',
            f'{postgres_port}:{postgres_port}',
            '--volume',
            f'{postgres_volume_name}:/data/postgres',
            '-e',
            f'POSTGRES_USER={postgres_username}',
            '-e',
            f'POSTGRES_PASSWORD={postgres_password}',
            postgres_image,
        ]
        logger.info(f"Starting postgres with command: {' '.join(command)}")
        _process = subprocess.Popen(command)
    else:
        raise NotImplementedError()
    return postgres_port


def kill_processes(processes: Set[int]):
    # Soft kill
    for pid in processes:
        logger.info(f'Killing {pid}')
        with suppress(ProcessLookupError):
            os.kill(pid, signal.SIGTERM)
    time.sleep(.1)

    # Force kill
    for pid in processes:
        logger.info(f'Force killing {pid}')
        with suppress(ProcessLookupError):
            os.kill(pid, signal.SIGKILL)


if __name__ == '__main__':
    free_frontend_port = find_next_free_port()
    free_backend_port = find_next_free_port(exclude_ports={free_frontend_port})
    start_fastapi_dev_server(free_backend_port, set(), Path(__file__).parents[2] / "fastapi_server")
    # start_svelte_dev_server(
    #     free_frontend_port,
    #     set(),
    #     Path(__file__).parents[2] / "svelte_frontend",
    #     backend_proxy=f'localhost:{free_backend_port}'
    # )
    # logger.info(f'Docker running: {check_if_docker_is_running()}')
    # logger.info(f'Postgres running: {check_if_postgres_is_running()}')

    # logger.info(f'MongoDB running: {check_if_mongodb_is_running()}')
    # start_postgres()
    # start_mongodb()
    while 1:
        time.sleep(1)
