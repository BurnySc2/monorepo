# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from collections import ChainMap
from pathlib import Path

from aiohttp.client import ClientSession
from hypothesis import given
from hypothesis import strategies as st

import python_examples.examples.async_await.asyncio_download_upload


@given(
    sites=st.one_of(
        st.lists(st.text()),
        st.sets(st.text()),
        st.frozensets(st.text()),
        st.dictionaries(keys=st.text(), values=st.text()),
        st.dictionaries(keys=st.text(), values=st.none()).map(dict.keys),  # type: ignore
        st.dictionaries(keys=st.integers(), values=st.text()).map(dict.values),  # type: ignore
        st.iterables(st.text()),
        st.dictionaries(keys=st.text(), values=st.text()).map(ChainMap),  # type: ignore
    )
)
def test_fuzz_download_all_sites(sites):
    python_examples.examples.async_await.asyncio_download_upload.download_all_sites(sites=sites)


@given(
    session=st.builds(ClientSession),
    url=st.text(),
    file_path=st.builds(Path),
    temp_file_path=st.builds(Path),
    download_speed=st.integers(),
    chunk_size=st.integers(),
)
def test_fuzz_download_file(session, url, file_path, temp_file_path, download_speed, chunk_size):
    python_examples.examples.async_await.asyncio_download_upload.download_file(
        session=session,
        url=url,
        file_path=file_path,
        temp_file_path=temp_file_path,
        download_speed=download_speed,
        chunk_size=chunk_size,
    )


@given(session=st.builds(ClientSession), url=st.text())
def test_fuzz_download_site(session, url):
    python_examples.examples.async_await.asyncio_download_upload.download_site(session=session, url=url)
