from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# https://pypi.org/project/dataclasses-json/#description
from dataclasses_json import DataClassJsonMixin


@dataclass()
class MyDataClass(DataClassJsonMixin):
    name: str
    value: int
    other: set[int]


@dataclass()
class MyDataClassList(DataClassJsonMixin):
    some_dataclasses: list[MyDataClass]
    other_dataclasses: list[MyDataClass]


def save_object_to_json(path: Path, my_dataclass_list: list[MyDataClass]):
    """Save the given list of objects to json file."""
    with path.open("w") as f:
        f.write(MyDataClass.schema().dumps(my_dataclass_list, many=True, indent=4))


def load_object_from_json(path: Path) -> list[MyDataClass]:
    """Load a json file and re-create a list of data class objects from it."""
    with path.open() as f:
        return MyDataClass.schema().loads(f.read(), many=True)


def save_objects_to_json(path: Path, my_dataclass_list: MyDataClassList):
    """Save the given data class object to json file."""
    with path.open("w") as f:
        f.write(my_dataclass_list.to_json(indent=4))


def load_objects_from_json(path: Path) -> MyDataClassList:
    """Load a json file and re-create a data class list object from it."""
    with path.open() as f:
        return MyDataClassList.from_json(f.read())


def test_data_class_to_and_from_json():
    """Creates a dataclass, saves to json, re-loads it from json file and compares them."""
    # Note: interestingly the class holds a set but the written json file contains a list
    # Reloading the list automatically converts it to a set again

    # Write and reload from file
    test_path = Path(__file__).parent.parent.parent / "data" / "dataclass_test.json"
    test_path.parent.mkdir(parents=True, exist_ok=True)

    # Create the objects we want to write
    my_first_object = MyDataClass("burny", 420, {1, 2, 3})
    my_second_object = MyDataClass("not_burny", 123, {4, 2, 0})

    # Method 1
    # Save
    data_class_list = [my_first_object, my_second_object]
    save_object_to_json(test_path, data_class_list)
    # Load and compare
    data_class_list_loaded = load_object_from_json(test_path)
    assert data_class_list_loaded == data_class_list
    assert data_class_list_loaded[0] == data_class_list[0]
    assert data_class_list_loaded[1] == data_class_list[1]

    # Method 2
    data_class_list_object = MyDataClassList([my_first_object], [my_second_object])
    # Save
    save_objects_to_json(test_path, data_class_list_object)
    # Load and compare
    data_class_list_object_loaded = load_objects_from_json(test_path)
    assert data_class_list_object_loaded == data_class_list_object
    assert data_class_list_object_loaded.some_dataclasses[0] == data_class_list_object.some_dataclasses[0]
    assert data_class_list_object_loaded.other_dataclasses[0] == data_class_list_object.other_dataclasses[0]
