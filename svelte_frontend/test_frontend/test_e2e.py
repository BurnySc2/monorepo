from typing import Optional, Set

import pytest
from pytest_benchmark.fixture import BenchmarkFixture
from seleniumbase import BaseCase

from burny_common.integration_test_helper import (
    find_next_free_port,
    get_website_address,
    kill_processes,
    start_svelte_dev_server,
)

# see https://github.com/seleniumbase/SeleniumBase
# https://seleniumbase.io/

# Set in setup_module()
FRONTEND_ADDRESS = ''
# Remember which node processes to close
NEWLY_CREATED_NODE_PROCESSES: Set[int] = set()


def setup_module():
    """
    See https://docs.pytest.org/en/6.2.x/xunit_setup.html
    """
    global FRONTEND_ADDRESS
    frontend_port = find_next_free_port()
    backend_port = find_next_free_port(exclude_ports={frontend_port})
    FRONTEND_ADDRESS = get_website_address(frontend_port)
    start_svelte_dev_server(frontend_port, NEWLY_CREATED_NODE_PROCESSES, backend_proxy=f'localhost:{backend_port}')


def teardown_module():
    # Stop frontend server
    kill_processes(NEWLY_CREATED_NODE_PROCESSES)
    NEWLY_CREATED_NODE_PROCESSES.clear()


class MyTestClass(BaseCase):

    def test_basic_site_display(self):
        """ Check if HOME site is visible """
        self.open(FRONTEND_ADDRESS)
        self.assert_text('BrowserStorage')

    def test_show_todos(self):
        """ Check if the to-do site is visible """
        self.open(FRONTEND_ADDRESS)
        self.click('#todo')
        self.assert_text('Unable to connect to server')

    def test_add_todo(self):
        """ Add a new to-do entry """
        self.open(FRONTEND_ADDRESS)
        self.click('#todo')
        self.assert_text('Unable to connect to server')
        test_text = 'my amazing test todo text'
        self.write('#newTodoInput', test_text)
        self.click('#submit1')
        self.assert_text(test_text)


class MyBenchClass(BaseCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.benchmark: Optional[BenchmarkFixture] = None

    @pytest.fixture(autouse=True)
    def setup_benchmark(self, benchmark):
        """
        Assign the benchmark to a class variable
        For more info see https://pytest-benchmark.readthedocs.io/en/latest/usage.html
        https://github.com/ionelmc/pytest-benchmark/blob/master/tests/test_with_testcase.py
        """
        self.benchmark = benchmark

    def basic_site_display(self):
        """ Check if HOME site is visible """
        self.open(FRONTEND_ADDRESS)
        self.assert_text('BrowserStorage')

    def test_bench_basic_site_display(self):
        """ Benchmark how fast the site loads """
        self.benchmark(self.basic_site_display)

    def add_todo(self):
        """ Add a new to-do entry """
        self.open(FRONTEND_ADDRESS)
        self.click('#todo')
        test_text = 'my amazing test todo text'
        self.write('#newTodoInput', test_text)
        self.click('#submit1')
        self.assert_text(test_text)

    def test_bench_add_todo(self):
        """ Benchmark how fast a to-do can be added """
        self.benchmark(self.add_todo)


if __name__ == '__main__':
    setup_module()
    teardown_module()
