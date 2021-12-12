import re
from typing import Dict, List, Union

import pymongo
from bson import ObjectId
from loguru import logger
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ServerSelectionTimeoutError
from pymongo.results import InsertManyResult, InsertOneResult


async def test_database_with_mongodb():
    my_port = 27017
    mongo_db_address = f'mongodb://localhost:{my_port}/'
    logger.info('Running mongodb test...')
    try:
        # Connect to client
        my_client: MongoClient
        with pymongo.MongoClient(mongo_db_address) as my_client:
            my_db_name = 'python-template-db'
            # Connect to db
            my_db: Database = my_client[my_db_name]
            # Check if db exists
            db_list: List[str] = my_client.list_database_names()
            if my_db_name in db_list:
                logger.info(f'The database exists: {my_db_name}')
                my_client.drop_database(my_db_name)
            # Check if collection exists
            collection_name = 'customers'
            col_list: List[str] = my_db.list_collection_names()
            if collection_name in col_list:
                logger.info(f'The collection exists: {collection_name}')

            # Drop all collections
            for col_name in col_list:
                col = my_db[col_name]
                col.drop()

            # Connect to collection
            my_col: Collection = my_db[collection_name]
            # Insert example
            my_dict = {'name': 'John', 'address': 'Some Highway 37'}
            result: InsertOneResult = my_col.insert_one(my_dict)
            logger.info(f'Inserted id: {result.inserted_id}')

            # Insert Many
            my_list = [
                {
                    'name': 'Amy',
                    'address': 'Some other mountain 22',
                },
                {
                    'name': 'Hannah',
                    'address': 'Some Mountain 21',
                },
                {
                    'name': 'Hannah',
                    'address': 'Some Mountain 27',
                },
            ]
            result: InsertManyResult = my_col.insert_many(my_list)
            logger.info(f'Inserted ids: {list(map(str, result.inserted_ids))}')
            assert len(result.inserted_ids) == 3

            # Find one
            _result: Dict[str, Union[ObjectId, str]] = my_col.find_one()
            # Find all
            assert len(list(my_col.find())) == 4

            # Find all with 'Mountain 21' in address
            _result = my_col.find({'address': 'Mountain 21'})

            # https://docs.mongodb.com/manual/reference/operator/query/
            # Find all that have 'Mountain' in address, like '%Mountain%'
            # Remove 2nd argument to be case sensitive
            my_regex = re.compile('.*Mountain.*', re.IGNORECASE)
            _result = my_col.find({'address': my_regex})

            # Only return (_id, name) of query
            _result = my_col.find({}, {'_id': 1, 'name': 1})

            # Sort by name ASC, then by address DESC, both below works
            # for i in my_col.find().sort("name", pymongo.ASCENDING).sort("address", pymongo.DESCENDING):
            for i in my_col.find().sort([
                ('name', pymongo.ASCENDING),
                ('address', pymongo.DESCENDING),
            ]):
                logger.info(f'MongoDB item: {i}')

            # Delete one
            assert len(list(my_col.find())) == 4
            my_col.delete_one({'address': my_regex})
            assert len(list(my_col.find())) == 3
            my_col.delete_many({'address': my_regex})
            assert len(list(my_col.find())) == 1

    except ServerSelectionTimeoutError:
        logger.warning(f"Could not find a running mongoDB instance on port '{my_port}' - aborting")
        logger.warning(
            "You can run mongodb by running: 'docker run --rm -d -p 27017-27019:27017-27019 --name mongodb mongo:5.0.0'",
        )
