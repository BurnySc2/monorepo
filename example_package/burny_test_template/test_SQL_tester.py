# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from hypothesis import given
from hypothesis import strategies as st

import example_package.burny_test_template.SQL_tester


@given(album_id=st.integers(), album_name=st.text(), publish_year=st.integers())
def test_fuzz_Album(album_id, album_name, publish_year):
    example_package.burny_test_template.SQL_tester.Album(
        album_id=album_id, album_name=album_name, publish_year=publish_year
    )


@given(
    artist_id=st.integers(),
    artist_name=st.text(),
    birth_year=st.integers(),
    verified=st.booleans(),
)
def test_fuzz_Artist(artist_id, artist_name, birth_year, verified):
    example_package.burny_test_template.SQL_tester.Artist(
        artist_id=artist_id,
        artist_name=artist_name,
        birth_year=birth_year,
        verified=verified,
    )


@given(
    song_id=st.integers(),
    song_name=st.text(),
    artist_id=st.integers(),
    album_id=st.integers(),
    genre=st.text(),
    song_length=st.integers(),
)
def test_fuzz_Song(song_id, song_name, artist_id, album_id, genre, song_length):
    example_package.burny_test_template.SQL_tester.Song(
        song_id=song_id,
        song_name=song_name,
        artist_id=artist_id,
        album_id=album_id,
        genre=genre,
        song_length=song_length,
    )
