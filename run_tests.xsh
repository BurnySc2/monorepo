#!/usr/bin/env xonsh
# In CI: xonsh run_tests.xsh run --pylint --pytest --npmlint --npmtest --all
# For dev: xonsh run_tests.xsh run --pylint --npmlint
# For dev (slower): xonsh run_tests.xsh run --pylint --pytest --npmlint --npmtest
from typing import List
from xonsh.tools import print_color
import xonsh.cli_utils as xcli

# $PATH.append($(pwd).strip())
# print($PATH)

python_projects = ["burny_common", "discord_bot", "fastapi_server", "python_examples"]
frontend_projects = ["bored_gems", "replay_comparer", "supabase_stream_scripts", "svelte_frontend"]
changed_files: List[str] = $(git diff HEAD --name-only).splitlines()

def has_changed_files(project_name: str) -> bool:
    return any(project_name in file_name for file_name in changed_files)

def format_and_lint_project(project_name: str, all_files: bool = False):
    if all_files:
        files = $(git ls-files '*.py').splitlines()
        files_related_to_project = [file_name for file_name in files
            if project_name in file_name]
    else:
        files_related_to_project = [file_name for file_name in changed_files
            if project_name in file_name and file_name.endswith(".py")]
    if not files_related_to_project:
        return
    # Autoformat
    print_color(f"Running {{GREEN}}yapf{{RESET}} in project {{GREEN}}'{project_name}'{{RESET}} on {len(files_related_to_project)} file(s)")
    poetry run yapf --in-place @(files_related_to_project)
    # Lint
    print_color(f"Running {{GREEN}}pylint{{RESET}} in project {{GREEN}}'{project_name}'{{RESET}} on {len(files_related_to_project)} file(s)")
    poetry run python -m pylint @(files_related_to_project)

def run_mypy():
    # Run mypy on all python files because types could have changed which can affect other files
    python_files = $(git ls-files '*.py').splitlines()
    print_color(f"Running {{GREEN}}mypy{{RESET}} on python files")
    poetry run mypy @(python_files)

def run(
        run_python_lint: xcli.Arg('--pylint', '-pl', action="store_true") = False,
        run_python_test: xcli.Arg('--pytest', '-pt', action="store_true") = False,
        run_npm_lint: xcli.Arg('--npmlint', '-nl', action="store_true") = False,
        run_npm_test: xcli.Arg('--npmtest', '-nt', action="store_true") = False,
        run_only_changed_files: xcli.Arg('--all', '-a', action="store_false") = True,
    ):

    if run_python_lint or run_python_test:
        if run_python_lint:
            run_mypy()
        for project_name in python_projects:
            if run_only_changed_files and not has_changed_files(project_name):
                continue
            if run_python_lint:
                format_and_lint_project(project_name, all_files=not run_only_changed_files)
            if run_python_test:
                poetry run python -m pytest @(project_name)
                if project_name in ["fastapi_server", "discord_bot"]:
                    print_color(f"Building {{GREEN}}docker image{{RESET}} in project {{GREEN}}'{project_name}'{{RESET}}")
                    cd @(project_name)
                    docker build --quiet --tag precommit_image . && docker rmi precommit_image
                    cd ..

    if run_npm_lint or run_npm_test:
        for project_name in frontend_projects:
            if run_only_changed_files and not has_changed_files(project_name):
                continue
            print_color(f"Running {{GREEN}}prettier, lint and tests{{RESET}} in project {{GREEN}}'{project_name}'{{RESET}}")
            cd @(project_name)
            if run_npm_lint and run_npm_test:
                # Add npm run format
                npm install && npm run lint && npm run build-precommit && npm run test
            if run_npm_lint:
                # npm run format # Fix me
                npm install && npm run lint
            elif run_npm_test:
                npm install && npm run build-precommit && npm run test
            cd ..
            if run_npm_test:
                if project_name in ["svelte_frontend"]:
                    poetry run python -m pytest svelte_frontend/test_frontend/test_e2e.py --benchmark-skip

if __name__ == '__main__':
    parser = xcli.make_parser("test commands")
    parser.add_command(run)
    xcli.dispatch(parser)
