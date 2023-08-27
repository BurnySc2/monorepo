from typing import Dict, Optional, Any


class Node:
    def __init__(self) -> None:
        self.children: Dict[str, Node] = {}
        self.value: Optional[Any] = None


class WordDictionary:
    def __init__(self):
        self.children = Node()

    def addWord(self, word: str) -> None:
        node = self.children
        for index, char in enumerate(word):
            if char not in node.children:
                node.children[char] = Node()
            node = node.children[char]
        node.value = word

    def insert(self, word: str) -> None:
        self.addWord(word)

    def startsWith(self, prefix: str) -> bool:
        node = self.children
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True

    def search(self, word: str, start_node: Optional[Node] = None) -> bool:
        """ Word can be 'asd' or 'a.d' which should match the same. """
        if start_node is not None:
            node = start_node
        else:
            node = self.children
        for index, char in enumerate(word):
            if char != "." and char not in node.children:
                return False
            if char == ".":
                return any(self.search(f"{key}{word[1+index:]}", node) for key in node.children.keys())
            node = node.children[char]
        return bool(node.value)


if __name__ == "__main__":
    obj = WordDictionary()
    word = "asdd"
    obj.addWord(word)
    param_2 = obj.search(word)
    print(param_2)
    param_2 = obj.search("as.d")
    print(param_2)
    param_2 = obj.search("as..d")
    print(param_2)

    obj.addWord("apple")
    assert obj.search("apple")
    assert not obj.search("app")
