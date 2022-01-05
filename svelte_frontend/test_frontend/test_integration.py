from pathlib import Path
from typing import Set

# see https://github.com/seleniumbase/SeleniumBase
# https://seleniumbase.io/
from seleniumbase import BaseCase

from burny_common.integration_test_helper import (
    find_next_free_port,
    get_website_address,
    kill_processes,
    remove_leftover_files,
    start_fastapi_dev_server,
    start_svelte_dev_server,
)


class MyTestClass(BaseCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.FRONTEND_ADDRESS = ''
        self.BACKEND_ADDRESS = ''
        # Remember which node processes to close
        self.NEWLY_CREATED_PROCESSES: Set[int] = set()
        # And which files to remove
        self.CREATED_FILES: Set[Path] = set()

    def setup_method(self, _method=None):
        """ setup any state tied to the execution of the given method in a
        class.  setup_method is invoked for every test method of a class.
        See https://docs.pytest.org/en/6.2.x/xunit_setup.html
        """
        free_frontend_port = find_next_free_port()
        free_backend_port = find_next_free_port(exclude_ports={free_frontend_port})
        self.FRONTEND_ADDRESS = get_website_address(free_frontend_port)
        self.BACKEND_ADDRESS = f'http://localhost:{free_backend_port}'
        start_fastapi_dev_server(free_backend_port, self.NEWLY_CREATED_PROCESSES, self.CREATED_FILES)
        start_svelte_dev_server(
            free_frontend_port,
            self.NEWLY_CREATED_PROCESSES,
            backend_proxy=f'localhost:{free_backend_port}',
        )
        # start_mongodb()
        # start_postgres()

    def teardown_method(self, _method=None):
        """ teardown any state that was previously setup with a setup_method
        call.
        """
        # Stop frontend + backend server
        kill_processes(self.NEWLY_CREATED_PROCESSES)
        self.NEWLY_CREATED_PROCESSES.clear()

        # Remove files created by test
        remove_leftover_files(self.CREATED_FILES)
        self.CREATED_FILES.clear()

    def test_backend_server_available(self):
        self.open(self.BACKEND_ADDRESS)
        self.assert_text('{"Hello":"World"}')

    def test_frontend_server_available(self):
        self.open(self.FRONTEND_ADDRESS)
        self.assert_text('Home')
        self.assert_text('About')
        self.assert_text('Chat')
        self.assert_text('Todo')
        self.assert_text('BrowserStorage')

    def test_add_todo_submit1(self):
        """ Add a new to-do entry """
        self.open(self.FRONTEND_ADDRESS)
        self.assert_text('Hello world!')
        self.click('#todo')
        self.assert_text_not_visible('Unable to connect to server - running local mode', timeout=1)
        test_text = 'my amazing test todo text1'
        self.assert_text_not_visible(test_text)
        self.write('#newTodoInput', test_text)
        self.click('#submit1')
        self.assert_text(test_text)
        self.assert_text_not_visible('Unable to connect to server - running local mode', timeout=1)

    def test_add_todo_submit2(self):
        """ Add a new to-do entry, same as above """
        self.open(self.FRONTEND_ADDRESS)
        self.assert_text('Hello world!')
        self.click('#todo')
        self.assert_text_not_visible('Unable to connect to server - running local mode', timeout=1)
        test_text = 'my amazing test todo text2'
        self.assert_text_not_visible(test_text)
        self.write('#newTodoInput', test_text)
        self.click('#submit2')
        self.assert_text(test_text)
        self.assert_text_not_visible('Unable to connect to server - running local mode', timeout=1)

    def test_add_todo_submit3(self):
        """ Add a new to-do entry, same as above """
        self.open(self.FRONTEND_ADDRESS)
        self.assert_text('Hello world!')
        self.click('#todo')
        self.assert_text_not_visible('Unable to connect to server - running local mode', timeout=1)
        test_text = 'my amazing test todo text3'
        self.assert_text_not_visible(test_text)
        self.write('#newTodoInput', test_text)
        self.click('#submit3')
        self.assert_text(test_text)
        self.assert_text_not_visible('Unable to connect to server - running local mode', timeout=1)

    def test_chat_single(self):
        """ Chat with yourself """
        self.open(self.FRONTEND_ADDRESS)
        self.assert_text('Hello world!')
        self.click('#chat')
        my_username = 'beep_boop'

        self.assert_text_not_visible(my_username)
        self.write('#username', my_username)
        self.click('#connect')

        # Send a message by pressing send button
        some_text = 'bla blubb'
        self.write('#chatinput', some_text)
        self.assert_text_not_visible('You')
        self.click('#sendmessage')
        self.assert_text('You')
        self.assert_text(some_text)
        # Send a message by pressing enter
        some_other_text = 'some other text'
        self.write('#chatinput', f'{some_other_text}\n')
        self.assert_text(some_other_text)

    def test_chat_two_people(self):
        """ Make sure chat between 2 people work """
        # Connect with robot1
        self.open(self.FRONTEND_ADDRESS)
        self.click('#chat')
        my_username1 = 'robot1'
        self.write('#username', my_username1)
        self.click('#connect')
        # Send message from robot1
        some_text1 = 'sometext1'
        self.write('#chatinput', some_text1)
        self.click('#sendmessage')
        self.assert_text('You')
        self.assert_text(some_text1)

        # Connect with robot2
        self.open_new_window(True)
        self.open(self.FRONTEND_ADDRESS)
        self.click('#chat')
        my_username2 = 'robot2'
        self.write('#username', my_username2)
        self.click('#connect')
        # Make sure robot1's messages are visible from robot2
        self.assert_text(my_username1)
        self.assert_text(some_text1)
        # Send message from robot2
        some_text2 = 'sometext2'
        self.write('#chatinput', some_text2)
        self.click('#sendmessage')
        self.assert_text('You')
        self.assert_text(some_text2)

        # Make sure robot2's messages are visible from robot1
        self.switch_to_window(0)
        self.assert_text(my_username2)
        self.assert_text(some_text2)

    def test_graphql_chat_single(self):
        """ Chat with yourself """
        self.open(self.FRONTEND_ADDRESS)
        self.assert_text('Hello world!')
        self.click('#graphqlchat')
        connect_text = 'Connect to graphql chat'
        self.assert_text(connect_text)

        my_username = 'beep_boop'
        self.assert_text_not_visible(my_username)
        self.write('#username', my_username)
        self.click('#connect')

        # Send a message by pressing send button
        some_text = 'bla blubb'
        self.write('#chatinput', some_text)
        self.assert_text_not_visible('You')
        self.click('#sendmessage')
        self.assert_text('You')
        self.assert_text(some_text)
        # Send a message by pressing enter
        some_other_text = 'some other text'
        self.write('#chatinput', f'{some_other_text}\n')
        self.assert_text(some_other_text)

        self.click('#leavechatroom')
        self.assert_text(connect_text)

    def test_graphql_chat_two_people(self):
        """ Make sure chat between 2 people work """
        # Connect with robot1
        self.open(self.FRONTEND_ADDRESS)
        self.click('#graphqlchat')
        my_username1 = 'robot1'
        self.write('#username', my_username1)
        self.click('#connect')
        # Send message from robot1
        some_text1 = 'sometext1'
        self.write('#chatinput', some_text1)
        self.click('#sendmessage')
        self.assert_text('You')
        self.assert_text(some_text1)

        # Connect with robot2
        self.open_new_window(True)
        self.open(self.FRONTEND_ADDRESS)
        self.click('#graphqlchat')
        my_username2 = 'robot2'
        self.write('#username', my_username2)
        self.click('#connect')
        # Make sure robot1's messages are visible from robot2
        self.assert_text(my_username1)
        self.assert_text(some_text1)
        # Send message from robot2
        some_text2 = 'sometext2'
        self.write('#chatinput', some_text2)
        self.click('#sendmessage')
        self.assert_text('You')
        self.assert_text(some_text2)

        # Make sure robot2's messages are visible from robot1
        self.switch_to_window(0)
        self.assert_text(my_username2)
        self.assert_text(some_text2)

        connect_text = 'Connect to graphql chat'
        self.assert_text_not_visible(connect_text)
        self.click('#leavechatroom')
        self.assert_text(connect_text)

        self.switch_to_window(1)
        self.assert_text_not_visible(connect_text)
        self.click('#leavechatroom')
        self.assert_text(connect_text)


if __name__ == '__main__':
    # This doesnt work anymore with classes, why?
    test = MyTestClass()
    test.setup_method()
    test.test_backend_server_available()
    test.teardown_method()
