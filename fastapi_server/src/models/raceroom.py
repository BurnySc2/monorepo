"""
Model for the best times for the game RaceRoom
https://game.raceroom.com
"""

import asyncio

from dotenv import load_dotenv
from piccolo.columns import (
    DoublePrecision,
    ForeignKey,
    Integer,
    Text,
    Timestamp,
)
from piccolo.table import Table, create_db_tables

load_dotenv()


class RRRETrack(Table, tablename="litestar_rrre_track"):
    track_id = Integer(unique=True)
    track_name = Text()


class RRREPlayer(Table, tablename="litestar_rrre_player"):
    player_id = Integer(unique=True)
    player_name = Text()


class RRREBestTime(Table, tablename="litestar_rrre_best_time"):
    player_id = ForeignKey(null=False, references=RRREPlayer, target_column=RRREPlayer.player_id)
    track_id = ForeignKey(null=False, references=RRRETrack, target_column=RRRETrack.track_id)
    car_class = Text()
    car_name = Text()
    # "Amateur", "Get Real" or "Novice"
    driving_model = Text()
    # When was this best time established?
    # Apparently this defaults to the driver's timezone or german timezone
    datetime_driven = Timestamp()
    # How good was the driver's time?
    best_time = DoublePrecision()


async def main():
    await create_db_tables(RRREPlayer, RRRETrack, RRREBestTime, if_not_exists=True)
    # Add unique constraint on best times
    await RRREBestTime.raw("""
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'unique_player_car_driving_track'
        AND conrelid = 'public.litestar_rrre_best_time'::regclass
    ) THEN
        ALTER TABLE public.litestar_rrre_best_time
        ADD CONSTRAINT unique_player_car_driving_track
        UNIQUE (player_id, car_name, driving_model, track_id);
    END IF;
END $$;
    """)


if __name__ == "__main__":
    asyncio.run(main())
