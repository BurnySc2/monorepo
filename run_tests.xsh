#!/usr/bin/env xonsh
"""
In CI:
xonsh run_tests.xsh run --pylint --npmlint --all --verbose
For dev (only changed files):
xonsh run_tests.xsh run --pylint --npmlint
For dev (slower):
xonsh run_tests.xsh run --pylint --pytest --npmlint --npmtest
For dev (slowest, run all tests):
xonsh run_tests.xsh run --pylint --pytest --npmlint --npmtest --all --verbose

'yapf' will be executed in the subfolder, but will use the style from the parent folder pyproject.toml
'pylint' will need explicitly be told to use config from parent folder via '--rcfile ../pyproject.toml'
'mypy' will need explicitly be told to use config from parent folder via '--config-file absolute_path/pyproject.toml'
"""
from typing import List, Tuple, Dict
from xonsh.procs.pipelines import CommandPipeline
from xonsh.tools import print_color
import xonsh.cli_utils as xcli
from pathlib import Path
import time
import sys

def convert_git_relative_path_to_absolute_path(git_response: str) -> List[str]:
    # E.g. input of "$(git ls-files '*.py')" or "$(git diff HEAD --name-only)"
    return list(map(
        lambda file: str(Path(file).absolute()),
        git_response.splitlines()
    ))

PYTHON_PROJECTS = ["fastapi_server", "discord_bot", "burny_common", "python_examples", "svelte_frontend"]
FRONTEND_PROJECTS = ["bored_gems", "replay_comparer", "supabase_stream_scripts", "svelte_frontend"]
CHANGED_FILES: List[str] = convert_git_relative_path_to_absolute_path($(git diff HEAD --name-only))
PYTHON_FILES: List[str] = convert_git_relative_path_to_absolute_path($(git ls-files '*.py'))
FILES_IN_PROJECT: Dict[str, List[str]] = {
        project_name: convert_git_relative_path_to_absolute_path($(git ls-files @(project_name)))
        for project_name in PYTHON_PROJECTS + FRONTEND_PROJECTS
    }
SCRIPTS_WITH_ERRORS: List[Tuple[str, str]] = []

MAIN_CONFIG_FILE: Path = (Path(__file__).parent / "pyproject.toml").absolute()
assert " " not in str(MAIN_CONFIG_FILE), "No spaces allowed in path to pyproject.toml"
PYCLN_CHECK_COMMAND = f"poetry run pycln -c --config {str(MAIN_CONFIG_FILE)}".split()
PYCLN_COMMAND = f"poetry run pycln --config {str(MAIN_CONFIG_FILE)}".split()
ISORT_CHECK_COMMAND = f"poetry run isort --check-only --cr {str(MAIN_CONFIG_FILE.parent)} --resolve-all-configs".split()
ISORT_COMMAND = f"poetry run isort --cr {str(MAIN_CONFIG_FILE.parent)} --resolve-all-configs".split()
YAPF_COMMAND = "poetry run yapf --in-place".split()
PYLINT_COMMAND = f"poetry run pylint --rcfile {str(MAIN_CONFIG_FILE)}".split()
MYPY_COMMAND = f"poetry run mypy --config-file {str(MAIN_CONFIG_FILE)}".split()

def project_has_changed_files(project_name: str, changed_only=True, file_ending: str="") -> List[str]:
    iterable_files = CHANGED_FILES if changed_only else FILES_IN_PROJECT[project_name]
    return [
        file_name for file_name in iterable_files
        if file_name.endswith(file_ending)
        # In CHANGED_FILES all changed files are located, but we want only the ones related to 'project_name'
        and file_name.startswith(f"{$(pwd).strip()}/{project_name}")
    ]

def replace_last_message(old_message: str, new_message: str) -> None:
    length_difference = max(0, len(old_message) - len(new_message))
    print_color(new_message + " " * length_difference)

def run_command(command: List[str], ignore_exit_status=False, verbose=False, display_name='') -> int:
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
    if ignore_exit_status:
        replace_last_message(last_message, f"{time_required:.3f} {{YELLOW}}COMPLETED{{RESET}} - {print_command}")
    elif ret.returncode == 0:
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
    if not ignore_exit_status and ret.returncode != 0:
        SCRIPTS_WITH_ERRORS.append((location, command_as_line))
    return ret.returncode

def run(
        run_python_lint: xcli.Arg('--pylint', '-pl', action="store_true") = False,
        run_python_test: xcli.Arg('--pytest', '-pt', action="store_true") = False,
        run_npm_lint: xcli.Arg('--npmlint', '-nl', action="store_true") = False,
        run_npm_test: xcli.Arg('--npmtest', '-nt', action="store_true") = False,
        run_only_changed_files: xcli.Arg('--all', '-a', action="store_false") = True,
        verbose: xcli.Arg('--verbose', '-v', action="store_true") = False,
    ):
    # Run cleanup, autoformat, pylint, mypy on all python projects
    for python_project in PYTHON_PROJECTS:
        cd @(python_project)
        # run_command("poetry update".split(), verbose=verbose)
        run_command("poetry install".split(), verbose=verbose)
        if run_python_lint:
            project_py_files = project_has_changed_files(python_project, changed_only=False, file_ending=".py")
            if project_py_files:
                # Run mypy on all python files because types could have changed which can affect other files
                run_command(MYPY_COMMAND + project_py_files, verbose=verbose, display_name=f"Run mypy on {python_project}")

            project_changed_py_files = project_has_changed_files(python_project, changed_only=run_only_changed_files, file_ending=".py")
            if project_changed_py_files:
                # run_command(PYCLN_CHECK_COMMAND + project_changed_py_files, verbose=verbose, display_name=f"Run pycln check on {python_project}")
                run_command(PYCLN_COMMAND + project_changed_py_files, verbose=verbose, display_name=f"Run pycln on {python_project}")
                # run_command(ISORT_CHECK_COMMAND + project_changed_py_files, verbose=verbose, display_name=f"Run isort check on {python_project}")
                run_command(ISORT_COMMAND + project_changed_py_files, verbose=verbose, display_name=f"Run isort on {python_project}")
                run_command(YAPF_COMMAND + project_changed_py_files, verbose=verbose, display_name=f"Run yapf on {python_project}")
                run_command(PYLINT_COMMAND + project_changed_py_files, verbose=verbose, display_name=f"Run pylint on {python_project}")
        cd ..

    # burny_common
    # TODO Write tests
    # files_related_to_project = project_has_changed_files("burny_common", changed_only=run_only_changed_files)
    # if files_related_to_project and run_python_test:
    #     cd burny_common
    #     run_command("poetry run python -m pytest".split(), verbose=verbose)
    #     cd ..

    # discord_bot
    files_related_to_project = project_has_changed_files("python_examples", changed_only=run_only_changed_files)
    if files_related_to_project and run_python_test:
        cd discord_bot
        run_command("poetry run python -m pytest".split(), verbose=verbose)
        run_command("docker build --tag precommit_image_discord_bot .".split(), verbose=verbose)
        cd ..

    # fastapi_server
    files_related_to_project = project_has_changed_files("fastapi_server", changed_only=run_only_changed_files)
    if files_related_to_project and run_python_test:
        cd fastapi_server
        run_command("poetry run python -m pytest".split(), verbose=verbose)
        # Check if the server can start at all
        run_command("docker build --tag burnysc2/fastapi_server:latest .".split(), verbose=verbose)
        # Run fastapi server for 5 seconds, expect exitcode 124 if timeout was reached and didn't crash before
        mkdir -p data
        returncode = run_command("timeout 5 sh run.sh".split(), ignore_exit_status=True, verbose=False)
        if returncode != 124:
            timeout 5 sh run.sh
            SCRIPTS_WITH_ERRORS.append(("fastapi_server", "timeout 5 sh sh.run"))
        cd ..

    # python_examples
    files_related_to_project = project_has_changed_files("python_examples", changed_only=run_only_changed_files)
    if files_related_to_project and run_python_test:
        cd python_examples
        run_command("poetry run python -m pytest".split(), verbose=verbose)
        cd ..

    # bored_gems
    files_related_to_project = project_has_changed_files("bored_gems", changed_only=run_only_changed_files)
    if files_related_to_project and (run_npm_lint or run_npm_test):
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
    if files_related_to_project and (run_npm_lint or run_npm_test):
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
    if files_related_to_project and (run_npm_lint or run_npm_test):
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
    if files_related_to_project and (run_npm_lint or run_npm_test):
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
            # Install fastapi backend
            cd fastapi_server
            run_command("poetry install".split(), verbose=verbose)
            cd ..
            cd svelte_frontend
            # Install e2e and integration tests for frontend
            run_command("poetry install".split(), verbose=verbose)
            run_command("poetry run playwright install".split(), verbose=verbose)
            run_command("poetry run pytest test_frontend/test_e2e.py --benchmark-skip".split(), verbose=verbose)
            run_command("poetry run pytest test_frontend/test_integration.py --benchmark-skip".split(), verbose=verbose)
            cd ..


if __name__ == '__main__':
    parser = xcli.make_parser("test commands")
    parser.add_command(run)
    xcli.dispatch(parser)
    if SCRIPTS_WITH_ERRORS:
        print(f"The following commands threw errors:")
        print('\n'.join(map(str, SCRIPTS_WITH_ERRORS)))
        sys.exit(1)
    sys.exit(0)
