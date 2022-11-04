from pathlib import Path
from typing import Set

from playwright.sync_api import BrowserContext, Page

from test_integration.integration_test_helper import (
    find_next_free_port,
    kill_processes,
    start_fastapi_dev_server,
    start_svelte_dev_server,
)

# Uncomment if you want to render frontend debugger
# import os
# os.environ["PWDEBUG"] = "1"

WEBSITE_IP = 'http://localhost'


def get_website_address(port: int) -> str:
    return f'{WEBSITE_IP}:{port}'


class TestClass:
    FRONTEND_ADDRESS = ''
    BACKEND_ADDRESS = ''
    # Remember which node processes to close
    NEWLY_CREATED_PROCESSES: Set[int] = set()

    def setup_method(self, _method=None):
        """ setup any state tied to the execution of the given method in a
        class.  setup_method is invoked for every test method of a class.
        See https://docs.pytest.org/en/6.2.x/xunit_setup.html
        """
        free_frontend_port = find_next_free_port()
        free_backend_port = find_next_free_port(exclude_ports={free_frontend_port})
        self.FRONTEND_ADDRESS = get_website_address(free_frontend_port)
        self.BACKEND_ADDRESS = f'http://localhost:{free_backend_port}'
        start_fastapi_dev_server(
            free_backend_port,
            self.NEWLY_CREATED_PROCESSES,
            Path(__file__).parents[2] / 'fastapi_server',
        )
        start_svelte_dev_server(
            free_frontend_port,
            self.NEWLY_CREATED_PROCESSES,
            Path(__file__).parents[2] / 'svelte_frontend',
            backend_proxy=f'localhost:{free_backend_port}',
        )

    def teardown_method(self, _method=None):
        """ teardown any state that was previously setup with a setup_method
        call.
        """
        # Stop frontend + backend server
        kill_processes(self.NEWLY_CREATED_PROCESSES)
        self.NEWLY_CREATED_PROCESSES.clear()

    def test_backend_server_available(self, page: Page):
        page.goto(self.BACKEND_ADDRESS, wait_until='networkidle')
        assert '{"Hello":"World"}' in page.content()

    def test_frontend_server_available(self, page: Page):
        page.goto(self.FRONTEND_ADDRESS, wait_until='networkidle')
        assert 'Home' in page.content()
        assert 'About' in page.content()
        assert 'Chat' in page.content()
        assert 'Todo' in page.content()
        assert 'Slugs' in page.content()
        assert 'BrowserStorage' in page.content()

    def test_add_todo_submit1(self, page: Page):
        """ Add a new to-do entry """
        page.goto(self.FRONTEND_ADDRESS, wait_until='networkidle')
        assert 'Hello world!' in page.content()
        page.click('#todo')
        page.wait_for_url('/todo', timeout=1_000)
        assert 'Unable to connect to server - running local mode' not in page.content()
        test_text = 'my amazing test todo text1'
        assert test_text not in page.content()
        page.wait_for_selector('#newTodoInput', timeout=1_000)
        page.fill('#newTodoInput', test_text)
        page.click('#submit1')
        page.wait_for_timeout(100)
        assert test_text in page.content()
        assert 'Unable to connect to server - running local mode' not in page.content()

    def test_add_todo_submit2(self, page: Page):
        """ Add a new to-do entry """
        page.goto(self.FRONTEND_ADDRESS, wait_until='networkidle')
        assert 'Hello world!' in page.content()
        page.click('#todo')
        page.wait_for_url('/todo', timeout=1_000)
        assert 'Unable to connect to server - running local mode' not in page.content()
        test_text = 'my amazing test todo text1'
        assert test_text not in page.content()
        page.fill('#newTodoInput', test_text)
        page.click('#submit2')
        page.wait_for_timeout(100)
        assert test_text in page.content()
        assert 'Unable to connect to server - running local mode' not in page.content()

    def test_add_todo_submit3(self, page: Page):
        """ Add a new to-do entry """
        page.goto(self.FRONTEND_ADDRESS, wait_until='networkidle')
        assert 'Hello world!' in page.content()
        page.click('#todo')
        page.wait_for_url('/todo', timeout=1_000)
        assert 'Unable to connect to server - running local mode' not in page.content()
        test_text = 'my amazing test todo text1'
        assert test_text not in page.content()
        page.fill('#newTodoInput', test_text)
        page.click('#submit3')
        page.wait_for_timeout(100)
        assert test_text in page.content()
        assert 'Unable to connect to server - running local mode' not in page.content()

    def test_chat_single(self, page: Page):
        """ Chat with yourself """
        page.goto(self.FRONTEND_ADDRESS, wait_until='networkidle')
        assert 'Hello world!' in page.content()
        page.click('#chat')
        page.wait_for_url('/normalchat', timeout=1_000)
        my_username = 'beep_boop'

        assert my_username not in page.content()
        page.fill('#username', my_username)
        page.click('#connect')

        # Send a message by pressing send button
        some_text = 'bla blubb'
        page.fill('#chatinput', some_text)
        assert 'You' not in page.content()
        page.click('#sendmessage')
        assert 'You' in page.content()
        assert some_text in page.content()
        # Send a message by pressing enter
        some_other_text = 'some other text'
        page.type('#chatinput', f'{some_other_text}\n')
        assert some_other_text in page.content()

    def test_chat_two_people(self, context: BrowserContext):
        """ Make sure chat between 2 people work """
        # Connect with robot1
        page1 = context.new_page()
        page1.goto(self.FRONTEND_ADDRESS)
        page2 = context.new_page()
        page2.goto(self.FRONTEND_ADDRESS)

        page1.click('#chat')
        page1.wait_for_url('/normalchat', timeout=1_000)
        my_username1 = 'robot1'
        page1.fill('#username', my_username1)
        page1.click('#connect')
        # Send message from robot1
        some_text1 = 'sometext1'
        page1.fill('#chatinput', some_text1)
        page1.click('#sendmessage')
        assert 'You' in page1.content()
        assert some_text1 in page1.content()

        # Connect with robot2
        page2.click('#chat')
        page2.wait_for_url('/normalchat')
        my_username2 = 'robot2'
        page2.fill('#username', my_username2)
        page2.click('#connect')
        # Make sure robot1's messages are visible from robot2
        assert my_username1 in page2.content()
        assert some_text1 in page2.content()
        # Send message from robot2
        some_text2 = 'sometext2'
        page2.fill('#chatinput', some_text2)
        page2.click('#sendmessage')
        assert 'You' in page2.content()
        assert some_text2 in page2.content()

        # Make sure robot2's messages are visible from robot1
        assert my_username2 in page1.content()
        assert some_text2 in page1.content()
