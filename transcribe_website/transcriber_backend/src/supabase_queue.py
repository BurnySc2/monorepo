from src.db import JobItem


def put(retry=0):
    """
    Put a new item into the queue
    """


def get() -> JobItem:
    """
    Get a new item from the queue that has not been started
    """
    # Get item from supabase
    # If no item: return (no jobs available)
    # Update the item on supabase (return if failure on updating, e.g. job was already taken by another service)


def finish(id: int, new_status="Success"):
    """
    Mark an item as finished - this can be either success or failure
    """
