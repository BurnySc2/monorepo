import sys
from pathlib import Path

# Be able to launch from root folder
from platform import platform

try:
    sys.path.append(str(Path(__file__).parents[1]))
except IndexError:
    pass

# Other
# Coroutines and multiprocessing
import asyncio
import time

# Type annotation / hints
from typing import List

import aiohttp

# Simple logging https://github.com/Delgan/loguru
from loguru import logger

# Local examples
from python_examples.examples.async_await.asyncio_download_upload import download_all_sites, download_file
from python_examples.examples.async_await.rate_limited_example import api_rate_limited_example
from python_examples.examples.databases.mongodb_example import test_database_with_mongodb
from python_examples.examples.databases.sqlalchemy_example import test_database_with_sqlalchemy
from python_examples.examples.databases.sqlite_example import test_database
from python_examples.examples.databases.sqlmodel_example import test_database_with_sqlmodel
from python_examples.examples.databases.tinydb_example import test_database_with_tinydb
from python_examples.examples.dataclasses_and_dicts.import_export_dataclass import test_data_class_to_and_from_json
from python_examples.examples.dataclasses_and_dicts.modify_dictionary import modify_dictionary
from python_examples.examples.other.file_interaction import create_file
from python_examples.examples.other.geometry_example import test_geometry_shapely
from python_examples.examples.other.image_manipulation import mass_convert_images
from python_examples.examples.other.mass_replace import main as mass_replace_main
from python_examples.examples.other.multiprocessing_example import do_math, do_multiprocessing
from python_examples.examples.other.regex_example import regex_match_test, test_all_roman_numbers
from python_examples.examples.plot_data.bokeh_plot import main as bokeh_plot_main
from python_examples.examples.plot_data.clean_up import main as clean_up_main
from python_examples.examples.plot_data.matplotlib_plot import main as matplotlib_plot_main
from python_examples.examples.plot_data.pandas_plot import main as pandas_plot_main
from python_examples.examples.plot_data.seaborn_plot import main as seaborn_plot_main
from python_examples.templates.async_timeout_function import main as async_timeout_main
from python_examples.templates.deprecate_a_function import main as deprecate_a_function_main
from python_examples.templates.error_suppression import main as error_suppression_main
from python_examples.templates.inspect_function import main as inspect_main

# SIGALRM doesn't work on windows
if not platform().lower().startswith('win'):
    from python_examples.templates.timeout_function import main as timeout_main

logger.remove()  # Remove previous default handlers
# Log to console
logger.add(sys.stdout, level='INFO')
# Log to file, max size 1 mb, max log file age 7 days before a new one gets created
logger.add('main.log', rotation='1 MB', retention='7 days', level='INFO')


def main_sync():
    asyncio.run(main())


async def main():
    logger.info('Simple {} logger output', 'loguru')

    regex_match_test()

    sites: List[str] = ['http://www.jython.org', 'https://www.python.org/'] * 80
    start_time = time.perf_counter()
    await download_all_sites(sites)

    # Download an image with download speed throttle
    async with aiohttp.ClientSession() as session:
        _result: bool = await download_file(
            session,
            url='https://file-examples.com/wp-content/uploads/2017/10/file_example_PNG_1MB.png',
            file_path=Path(__file__).parent / 'data' / 'image.png',
            temp_file_path=Path(__file__).parent / 'data' / 'image_download_not_complete',
            # Download at speed of 100kb/s
            download_speed=100 * 2**10,
        )
    # Gather a ton of responses from an API
    await api_rate_limited_example()

    end_time = time.perf_counter()
    logger.info(f'Time for sites download taken: {end_time - start_time}')

    _math_result = do_math(6)

    start_time = time.perf_counter()
    _result2 = do_multiprocessing()
    end_time = time.perf_counter()
    logger.info(f'Time for multiprocessing taken: {end_time - start_time}')

    mass_replace_main()

    logger.info('Creating hello world file...')
    create_file()

    logger.info('Testing writing dataclass to json and re-load and compare both objects')
    test_data_class_to_and_from_json()

    modify_dictionary()

    logger.info('Validating all roman numbers up to 3999')
    test_all_roman_numbers()

    test_geometry_shapely()

    # TODO Table printing / formatting without library: print table (2d array) with 'perfect' row width

    logger.info('Converting all .jpg images in /images folder')
    mass_convert_images()

    logger.info('Testing database interaction')
    test_database()
    test_database_with_sqlalchemy()
    test_database_with_tinydb()
    test_database_with_sqlmodel()
    await test_database_with_mongodb()

    logger.info('Running template files')
    await async_timeout_main()
    deprecate_a_function_main()
    error_suppression_main()
    inspect_main()
    # SIGALRM doesn't work on windows
    if not platform().lower().startswith('win'):
        timeout_main()

    logger.info('Test plotting data')
    matplotlib_plot_main()
    bokeh_plot_main()
    pandas_plot_main()
    seaborn_plot_main()
    clean_up_main()


if __name__ == '__main__':
    main_sync()
