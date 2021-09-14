from dataclasses import dataclass, field
from enum import Enum
from typing import List

from loguru import logger


class NodeOutcome(Enum):
    NULL = 0
    SUCCESS = 1
    FAIL = 2
    RUNNING = 3


@dataclass
class ActionNode:
    child_actions: List['ActionNode'] = field(default_factory=list)
    continue_on_success: bool = True
    continue_on_fail: bool = False

    def run(self) -> NodeOutcome:
        outcome = self.run_node()
        if outcome == NodeOutcome.RUNNING:
            return NodeOutcome.RUNNING
        if outcome == NodeOutcome.FAIL:
            return NodeOutcome.FAIL

        for child_node in self.child_actions:
            child_outcome = child_node.run()
            if child_outcome == NodeOutcome.RUNNING:
                return NodeOutcome.RUNNING

            if child_outcome == NodeOutcome.SUCCESS and not self.continue_on_success:
                return outcome

            if child_outcome == NodeOutcome.FAIL and not self.continue_on_fail:
                return outcome

        return outcome

    def run_node(self) -> NodeOutcome:
        """ Run your code here """
        _self = self
        return NodeOutcome.SUCCESS

    def print_tree(self):
        """ TODO: output tree to console """

    def display_tree(self):
        """ TODO: output tree to display/monitor via matplotlib or graphviz or similar """


if __name__ == '__main__':

    class MyAction(ActionNode):
        my_status: int = 0

        def run_node(self) -> NodeOutcome:
            self.my_status += 1
            logger.info(f'Counting up: {self.my_status}')
            if self.my_status != 10:
                return NodeOutcome.RUNNING
            return NodeOutcome.SUCCESS

    some_action = MyAction()
    my_root_node = ActionNode([some_action])

    while 1:
        result = my_root_node.run()
        if result == NodeOutcome.SUCCESS:
            break
