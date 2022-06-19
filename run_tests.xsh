#!/usr/bin/env xonsh
# In CI:
# xonsh run_tests.xsh run --pylint --npmlint --all --verbose
# For dev (only changed files):
# xonsh run_tests.xsh run --pylint --npmlint
# For dev (slower):
# xonsh run_tests.xsh run --pylint --pytest --npmlint --npmtest
# For dev (slowest, run all tests):
# xonsh run_tests.xsh run --pylint --pytest --npmlint --npmtest --all --verbose
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

def project_has_changed_files(project_name: str, changed_only=True, file_ending: str="") -> List[str]:
    iterable_files = changed_files if changed_only else files_in_project(project_name)
    return [
        file_name for file_name in iterable_files
        if file_name.endswith(file_ending)
    ]

def replace_last_message(old_message: str, new_message: str) -> None:
    length_difference = max(0, len(new_message) - len(old_message))
    print_color(new_message + " " * length_difference)

def run_command(command: List[str], ignore_exit_status=False, verbose=False, display_name='') -> int:
    global ANY_COMMAND_HAS_ERROR
    start_time = time.perf_counter()
    location = $(pwd).strip()
    command_as_line = " ".join(command)
    print_command = display_name if display_name else f"{location} - {command_as_line}"
    last_message = f"\r{{YELLOW}}RUNNING{{RESET}} - {print_command}"
    print_color(last_message, end='\r')
    if verbose:
        ret: CommandPipeline = !(@(command))
    else:
        ret: CommandPipeline = !(@(command) 1>/dev/null 2>/dev/null)
    while $(jobs): # Without this, time.perf_counter() doesnt seem to work properly
        time.sleep(0.01)
    time_required: float = time.perf_counter() - start_time
    if ignore_exit_status or ret.returncode == 0:
        replace_last_message(last_message, f"{time_required:.3f} {{GREEN}}SUCCESS{{RESET}} - {print_command}")
    else:
        replace_last_message(last_message, f"{time_required:.3f} {{RED}}FAILURE{{RESET}} - {print_command} - Exited with exit code {ret.returncode}")
        print_color(f"{{RED}}FAILURE{{RESET}} Command executed in {location}:\n{command_as_line}")
        if verbose:
            print(f"STDOUT:\n{ret.out}\n")
            print(f"STDERR:\n{ret.err}\n")
        else:
            # Run command again in verbose mode
            @(command)
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
    global ANY_COMMAND_HAS_ERROR
    if run_python_lint:
        # Run mypy on all python files because types could have changed which can affect other files
        command = "poetry run mypy".split() + python_files
        run_command(command, verbose=verbose, display_name="Run mypy")

    # burny_common
    files_related_to_project = project_has_changed_files("burny_common", changed_only=run_only_changed_files)
    if files_related_to_project:
        if run_python_lint:
            files_related_to_project_py = project_has_changed_files("burny_common", changed_only=run_only_changed_files, file_ending=".py")
            run_command("poetry run yapf --in-place".split() + files_related_to_project_py, verbose=verbose, display_name="Run yapf on burny_common")
            run_command("poetry run pylint".split() + files_related_to_project_py, verbose=verbose, display_name="Run pylint on burny_common")

    # discord_bot
    files_related_to_project = project_has_changed_files("python_examples", changed_only=run_only_changed_files)
    if files_related_to_project:
        if run_python_lint:
            files_related_to_project_py = project_has_changed_files("python_examples", changed_only=run_only_changed_files, file_ending=".py")
            run_command("poetry run yapf --in-place".split() + files_related_to_project_py, verbose=verbose, display_name="Run yapf on discord_bot")
            run_command("poetry run pylint".split() + files_related_to_project_py, verbose=verbose, display_name="Run pylint on discord_bot")
        if run_python_test:
            cd discord_bot
            run_command("poetry install".split(), verbose=verbose)
            run_command("poetry run python -m pytest".split(), verbose=verbose)
            run_command("docker build --tag precommit_image_discord_bot .".split(), verbose=verbose)
            cd ..

    # fastapi_server
    files_related_to_project = project_has_changed_files("fastapi_server", changed_only=run_only_changed_files)
    if files_related_to_project:
        if run_python_lint:
            files_related_to_project_py = project_has_changed_files("fastapi_server", changed_only=run_only_changed_files, file_ending=".py")
            run_command("poetry run yapf --in-place".split() + files_related_to_project_py, verbose=verbose, display_name="Run yapf on fastapi_server")
            run_command("poetry run pylint".split() + files_related_to_project_py, verbose=verbose, display_name="Run pylint on fastapi_server")
        if run_python_test:
            cd fastapi_server
            run_command("poetry install".split(), verbose=verbose)
            run_command("poetry run python -m pytest".split(), verbose=verbose)
            # Check if the server can start at all
            run_command("docker build --tag burnysc2/fastapi_server:latest .".split(), verbose=verbose)
            # Run fastapi server for 5 seconds, expect exitcode 124 if timeout was reached and didn't crash before
            returncode = run_command("timeout 5 sh run.sh".split(), ignore_exit_status=True, verbose=verbose)
            if returncode == 124:
                ANY_COMMAND_HAS_ERROR = True
            cd ..

    # python_examples
    files_related_to_project = project_has_changed_files("python_examples", changed_only=run_only_changed_files)
    if files_related_to_project:
        if run_python_lint:
            files_related_to_project_py = project_has_changed_files("python_examples", changed_only=run_only_changed_files, file_ending=".py")
            run_command("poetry run yapf --in-place".split() + files_related_to_project_py, verbose=verbose, display_name="Run yapf on python_examples")
            run_command("poetry run pylint".split() + files_related_to_project_py, verbose=verbose, display_name="Run pylint on python_examples")
        if run_python_test:
            cd python_examples
            run_command("poetry install".split(), verbose=verbose)
            run_command("poetry run python -m pytest".split(), verbose=verbose)
            cd ..

    # bored_gems
    files_related_to_project = project_has_changed_files("bored_gems", changed_only=run_only_changed_files)
    if files_related_to_project:
        cd bored_gems
        run_command("npm install".split(), verbose=verbose)
        if run_npm_lint:
            run_command("npm run format".split(), verbose=verbose)
            run_command("npm run lint".split(), verbose=verbose)
        if run_npm_test:
            run_command("npx playwright install".split(), verbose=verbose)
            run_command("npm run build".split(), verbose=verbose)
            run_command("npm run test".split(), verbose=verbose)
        cd ..

    # replay_comparer
    files_related_to_project = project_has_changed_files("replay_comparer", changed_only=run_only_changed_files)
    if files_related_to_project:
        cd replay_comparer
        run_command("npm install".split(), verbose=verbose)
        if run_npm_lint:
            run_command("npm run format".split(), verbose=verbose)
            run_command("npm run lint".split(), verbose=verbose)
        if run_npm_test:
            run_command("npm run build".split(), verbose=verbose)
            run_command("npm run test".split(), verbose=verbose)
        cd ..

    # supabase_stream_scripts
    files_related_to_project = project_has_changed_files("supabase_stream_scripts", changed_only=run_only_changed_files)
    if files_related_to_project:
        cd supabase_stream_scripts
        run_command("npm install".split(), verbose=verbose)
        if run_npm_lint:
            run_command("npm run format".split(), verbose=verbose)
            run_command("npm run lint".split(), verbose=verbose)
        if run_npm_test:
            run_command("npm run build".split(), verbose=verbose)
            run_command("npm run test".split(), verbose=verbose)
        cd ..

    # svelte_frontend
    files_related_to_project = project_has_changed_files("svelte_frontend", changed_only=run_only_changed_files)
    if files_related_to_project:
        cd svelte_frontend
        run_command("npm install".split(), verbose=verbose)
        if run_npm_lint:
            run_command("npm run format".split(), verbose=verbose)
            run_command("npm run lint".split(), verbose=verbose)
        if run_npm_test:
            run_command("npm run build".split(), verbose=verbose)
            run_command("npm run test".split(), verbose=verbose)
        cd ..
        if run_npm_test:
            cd fastapi_server
            run_command("poetry install".split(), verbose=verbose)
            run_command("poetry run playwright install".split(), verbose=verbose)
            run_command("poetry run python -m pytest ../svelte_frontend/test_frontend/test_e2e.py --benchmark-skip".split(), verbose=verbose)
            run_command("poetry run python -m pytest ../svelte_frontend/test_frontend/test_integration.py --benchmark-skip".split(), verbose=verbose)
            cd ..


if __name__ == '__main__':
    parser = xcli.make_parser("test commands")
    parser.add_command(run)
    xcli.dispatch(parser)
    if ANY_COMMAND_HAS_ERROR:
        sys.exit(1)
    sys.exit(0)
