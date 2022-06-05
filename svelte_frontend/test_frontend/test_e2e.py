from typing import Set

from playwright.sync_api import Page

from burny_common.integration_test_helper import (
    find_next_free_port,
    get_website_address,
    kill_processes,
    start_svelte_dev_server,
)

# Set in setup_module()
FRONTEND_ADDRESS = ''
# Remember which node processes to close
NEWLY_CREATED_NODE_PROCESSES: Set[int] = set()


def setup_module():
    """
    See https://docs.pytest.org/en/6.2.x/xunit_setup.html
    """
    # pylint: disable=W0603
    global FRONTEND_ADDRESS
    frontend_port = find_next_free_port()
    backend_port = find_next_free_port(exclude_ports={frontend_port})
    FRONTEND_ADDRESS = get_website_address(frontend_port)
    start_svelte_dev_server(frontend_port, NEWLY_CREATED_NODE_PROCESSES, backend_proxy=f'localhost:{backend_port}')


def teardown_module():
    # Stop frontend server
    kill_processes(NEWLY_CREATED_NODE_PROCESSES)
    NEWLY_CREATED_NODE_PROCESSES.clear()


class TestClass:

    def test_basic_site_display(self, page: Page):
        """ Check if HOME site is visible """
        page.goto(FRONTEND_ADDRESS)
        assert 'BrowserStorage' in page.content()
        assert page.inner_text('#browserstorage') == 'BrowserStorage'

    def test_show_todos(self, page: Page):
        """ Check if the to-do site is visible """
        page.goto(FRONTEND_ADDRESS)
        page.click('#todo')
        page.wait_for_url('/todo')
        page.wait_for_timeout(100)
        assert 'Unable to connect to server' in page.content()

    def test_add_todo(self, page: Page):
        """ Add a new to-do entry """
        page.goto(FRONTEND_ADDRESS)
        page.click('#todo')
        page.wait_for_url('/todo')
        page.wait_for_timeout(100)
        assert 'Unable to connect to server' in page.content()
        test_text = 'my amazing test todo text'
        page.fill('#newTodoInput', test_text)
        page.click('#submit1')
        assert test_text in page.content()


# TODO Redo benchmarking in playwright

# class TestBenchClass:
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.benchmark: Optional[BenchmarkFixture] = None
#
#     @pytest.fixture(autouse=True)
#     def setup_benchmark(self, benchmark):
#         """
#         Assign the benchmark to a class variable
#         For more info see https://pytest-benchmark.readthedocs.io/en/latest/usage.html
#         https://github.com/ionelmc/pytest-benchmark/blob/master/tests/test_with_testcase.py
#         """
#         self.benchmark = benchmark
#
#     def basic_site_display(self):
#         """ Check if HOME site is visible """
#         self.open(FRONTEND_ADDRESS)
#         self.assert_text('BrowserStorage')
#
#     def test_bench_basic_site_display(self):
#         """ Benchmark how fast the site loads """
#         self.benchmark(self.basic_site_display)
#
#     def add_todo(self):
#         """ Add a new to-do entry """
#         self.open(FRONTEND_ADDRESS)
#         self.click('#todo')
#         test_text = 'my amazing test todo text'
#         self.write('#newTodoInput', test_text)
#         self.click('#submit1')
#         self.assert_text(test_text)
#
#     def test_bench_add_todo(self):
#         """ Benchmark how fast a to-do can be added """
#         self.benchmark(self.add_todo)

if __name__ == '__main__':
    setup_module()
    teardown_module()
