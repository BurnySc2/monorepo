#!/usr/bin/env xonsh
# In CI:
# poetry run xonsh run_tests.xsh run --pylint --pytest --npmlint --npmtest --all --verbose
# For dev (only changed files):
# poetry run xonsh run_tests.xsh run --pylint --npmlint
# For dev (slower):
# poetry run xonsh run_tests.xsh run --pylint --pytest --npmlint --npmtest
from typing import List
from xonsh.procs.pipelines import CommandPipeline
from xonsh.tools import print_color
import xonsh.cli_utils as xcli
import time
import sys

changed_files: List[str] = $(git diff HEAD --name-only).splitlines()
python_files: List[str] = $(git ls-files '*.py').splitlines()
files_in_project = lambda project_name: $(git ls-files @(project_name)).splitlines()
ANY_COMMAND_HAS_ERROR = False

def remove_last_message(message: str) -> None:
    print(" " * len(message), end="\r")

def run_command(command: List[str], ignore_exit_status=False, verbose=False, display_name='') -> int:
    global ANY_COMMAND_HAS_ERROR
    start_time = time.perf_counter()
    location = $(pwd).strip()
    command_as_line = " ".join(command)
    print_command = display_name if display_name else f"{location} - {command_as_line}"
    message = f"\r{{YELLOW}}RUNNING{{RESET}} - {print_command}"
    print_color(message, end='\r')
    if verbose:
        ret: CommandPipeline = !(@(command))
    else:
        ret: CommandPipeline = !(@(command) 1>/dev/null 2>/dev/null)
    while $(jobs): # Without this, time.perf_counter() doesnt seem to work properly
        time.sleep(0.1)
    time_required: float = time.perf_counter() - start_time
    if ignore_exit_status or ret.returncode == 0:
        remove_last_message(message)
        print_color(f"{time_required:.3f} {{GREEN}}SUCCESS{{RESET}} - {print_command}")
    else:
        remove_last_message(message)
        print_color(f"{time_required:.3f} {{RED}}ERROR{{RESET}} - {print_command} - Exited with exit code {ret.returncode}")
        print_color(f"{{RED}}ERROR{{RESET}} Command executed in {location}:\n{command_as_line}")
        if verbose:
            print(f"STDOUT:\n{ret.out}\n")
            print(f"STDERR:\n{ret.err}\n")
        else:
            # Run command again in verbose mode
            @(command)
    if ignore_exit_status:
        return 0
    if ret.returncode != 0:
        ANY_COMMAND_HAS_ERROR = True
    return ret.returncode

def run(
        run_python_lint: xcli.Arg('--pylint', '-pl', action="store_true") = False,
        run_python_test: xcli.Arg('--pytest', '-pt', action="store_true") = False,
        run_npm_lint: xcli.Arg('--npmlint', '-nl', action="store_true") = False,
        run_npm_test: xcli.Arg('--npmtest', '-nt', action="store_true") = False,
        run_only_changed_files: xcli.Arg('--all', '-a', action="store_false") = True,
        verbose: xcli.Arg('--verbose', '-v', action="store_true") = False,
    ):
    if run_python_lint:
        # Run mypy on all python files because types could have changed which can affect other files
        command = "poetry run mypy".split() + python_files
        run_command(command, verbose=verbose, display_name="Run mypy")

    # burny_common
    if run_only_changed_files:
        files_related_to_project = [file_name for file_name in changed_files if "burny_common" in file_name]
    else:
        files_related_to_project = [file_name for file_name in python_files if "burny_common" in file_name]
    if files_related_to_project:
        if run_python_lint:
            run_command("poetry run yapf --in-place".split() + files_related_to_project, verbose=verbose, display_name="Run yapf on burny_common")
            run_command("poetry run pylint".split() + files_related_to_project, verbose=verbose, display_name="Run pylint on burny_common")

    # discord_bot
    if run_only_changed_files:
        files_related_to_project = [file_name for file_name in changed_files if "discord_bot" in file_name]
    else:
        files_related_to_project = [file_name for file_name in python_files if "discord_bot" in file_name]
    if files_related_to_project:
        if run_python_lint:
            run_command("poetry run yapf --in-place".split() + files_related_to_project, verbose=verbose, display_name="Run yapf on discord_bot")
            run_command("poetry run pylint".split() + files_related_to_project, verbose=verbose, display_name="Run pylint on discord_bot")
        if run_python_test:
            run_command("poetry run python -m pytest discord_bot".split(), verbose=verbose, display_name="Run pytest on discord_bot")
            cd discord_bot
            run_command("docker build --tag precommit_image_discord_bot .".split(), verbose=verbose, display_name="Build docker image in discord_bot")
            cd ..

    # fastapi_server
    if run_only_changed_files:
        files_related_to_project = [file_name for file_name in changed_files if "fastapi_server" in file_name]
    else:
        files_related_to_project = [file_name for file_name in python_files if "fastapi_server" in file_name]
    if files_related_to_project:
        if run_python_lint:
            run_command("poetry run yapf --in-place".split() + files_related_to_project, verbose=verbose, display_name="Run yapf on fastapi_server")
            run_command("poetry run pylint".split() + files_related_to_project, verbose=verbose, display_name="Run pylint on fastapi_server")
        if run_python_test:
            run_command("poetry run python -m pytest fastapi_server".split(), verbose=verbose, display_name="Run pytest on fastapi_server")
            cd fastapi_server
            run_command("docker build --tag precommit_image_fastapi_server .".split(), verbose=verbose, display_name="Build docker image in fastapi_server")
            cd ..

    # python_examples
    if run_only_changed_files:
        files_related_to_project = [file_name for file_name in changed_files if "python_examples" in file_name]
    else:
        files_related_to_project = [file_name for file_name in python_files if "python_examples" in file_name]
    if files_related_to_project:
        if run_python_lint:
            run_command("poetry run yapf --in-place".split() + files_related_to_project, verbose=verbose, display_name="Run yapf on python_examples")
            run_command("poetry run pylint".split() + files_related_to_project, verbose=verbose, display_name="Run pylint on python_examples")
        if run_python_test:
            run_command("poetry run python -m pytest python_examples".split(), verbose=verbose, display_name="Run pytest on python_examples")

    # bored_gems
    if run_only_changed_files:
        files_related_to_project = [file_name for file_name in changed_files if "bored_gems" in file_name]
    else:
        files_related_to_project = files_in_project("bored_gems")
    if files_related_to_project:
        cd bored_gems
        npm install 1>/dev/null 2>/dev/null
        npx playwright install 1>/dev/null 2>/dev/null
        playwright install 1>/dev/null 2>/dev/null
        if run_npm_lint:
            run_command("npm run format".split(), verbose=verbose)
            run_command("npm run lint".split(), verbose=verbose)
        if run_npm_test:
            run_command("npm run build".split(), verbose=verbose)
            run_command("npm run test".split(), verbose=verbose)
        cd ..

    # replay_comparer
    if run_only_changed_files:
        files_related_to_project = [file_name for file_name in changed_files if "replay_comparer" in file_name]
    else:
        files_related_to_project = files_in_project("replay_comparer")
    if files_related_to_project:
        cd replay_comparer
        npm install 1>/dev/null 2>/dev/null
        if run_npm_lint:
            run_command("npm run format".split(), verbose=verbose)
            run_command("npm run lint".split(), verbose=verbose)
        if run_npm_test:
            run_command("npm run build".split(), verbose=verbose)
            run_command("npm run test".split(), verbose=verbose)
        cd ..

    # supabase_stream_scripts
    if run_only_changed_files:
        files_related_to_project = [file_name for file_name in changed_files if "supabase_stream_scripts" in file_name]
    else:
        files_related_to_project = files_in_project("supabase_stream_scripts")
    if files_related_to_project:
        cd supabase_stream_scripts
        npm install 1>/dev/null 2>/dev/null
        if run_npm_lint:
            run_command("npm run format".split(), verbose=verbose)
            run_command("npm run lint".split(), verbose=verbose)
        if run_npm_test:
            run_command("npm run build".split(), verbose=verbose)
            run_command("npm run test".split(), verbose=verbose)
        cd ..

    # svelte_frontend
    if run_only_changed_files:
        files_related_to_project = [file_name for file_name in changed_files if "svelte_frontend" in file_name]
    else:
        files_related_to_project = files_in_project("svelte_frontend")
    if files_related_to_project:
        cd svelte_frontend
        npm install 1>/dev/null 2>/dev/null
        npx playwright install 1>/dev/null 2>/dev/null
        playwright install 1>/dev/null 2>/dev/null
        if run_npm_lint:
            run_command("npm run format".split(), verbose=verbose)
            run_command("npm run lint".split(), verbose=verbose)
        if run_npm_test:
            run_command("npm run build".split(), verbose=verbose)
            run_command("npm run test".split(), verbose=verbose)
        cd ..
        if run_npm_test:
            run_command("poetry run python -m pytest svelte_frontend/test_frontend/test_e2e.py --benchmark-skip".split(), verbose=verbose)

if __name__ == '__main__':
    parser = xcli.make_parser("test commands")
    parser.add_command(run)
    xcli.dispatch(parser)
    if ANY_COMMAND_HAS_ERROR:
        sys.exit(1)

