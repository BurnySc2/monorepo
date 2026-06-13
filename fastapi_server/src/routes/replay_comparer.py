from dataclasses import dataclass
from io import BytesIO
from typing import Annotated

import sc2reader
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

replay_comparer_router = APIRouter()

WORKER_UNIT_TYPES = {
    "SCV",
    "Probe",
    "Drone",
    "MULE",
}


@dataclass
class PlayerTimelineState:
    name: str = ""
    workers_active: int = 0
    workers_produced: int = 0
    workers_lost: int = 0
    workers_killed: int = 0
    total_resources_lost: int = 0
    total_resources_collected: int = 0
    last_minerals: int = 0
    last_vespene: int = 0


@dataclass
class TimelineDataPoint:
    gameloop: int
    workers_active: int
    workers_produced: int
    workers_lost: int
    supply: float
    supply_cap: float
    supply_block: int
    spm: float
    total_army_value: int
    total_resources_lost: int
    total_resources_collected: int
    workers_killed: int
    resource_collection_rate_all: int


@dataclass
class PlayerStatsAtFrame:
    frame: int
    pid: int
    workers_active: int = 0
    minerals_current: int = 0
    vespene_current: int = 0
    minerals_collection_rate: int = 0
    vespene_collection_rate: int = 0
    food_used: float = 0.0
    food_made: float = 0.0
    minerals_lost: int = 0
    vespene_lost: int = 0
    minerals_killed: int = 0
    vespene_killed: int = 0
    minerals_used_active_forces: int = 0
    vespene_used_active_forces: int = 0


@dataclass
class WorkerEvent:
    frame: int
    pid: int
    is_born: bool
    unit_type_name: str


def is_worker_unit(unit_type_name: str) -> bool:
    return unit_type_name in WORKER_UNIT_TYPES


def parse_replay_timeline(
    data: BytesIO, replay_tick: int
) -> tuple[list[PlayerTimelineState], list[list[TimelineDataPoint]]]:
    replay: sc2reader.resources.Replay = sc2reader.load_replay(data, load_level=3)  # type: ignore[attr-defined]

    players: list[PlayerTimelineState] = []
    player_pids: list[int] = []

    for team in replay.teams:
        for player in team.players:
            player_pids.append(player.pid)
            state = PlayerTimelineState(name=player.name)
            players.append(state)

    stats_events: list[PlayerStatsAtFrame] = []
    worker_events: list[WorkerEvent] = []

    for event in replay.tracker_events:
        frame = event.frame

        if isinstance(event, sc2reader.events.PlayerStatsEvent):
            stats_events.append(
                PlayerStatsAtFrame(
                    frame=frame,
                    pid=event.pid,
                    workers_active=event.workers_active_count,
                    minerals_current=event.minerals_current,
                    vespene_current=event.vespene_current,
                    minerals_collection_rate=event.minerals_collection_rate,
                    vespene_collection_rate=event.vespene_collection_rate,
                    food_used=event.food_used,
                    food_made=event.food_made,
                    minerals_lost=event.minerals_lost,
                    vespene_lost=event.vespene_lost,
                    minerals_killed=event.minerals_killed,
                    vespene_killed=event.vespene_killed,
                    minerals_used_active_forces=event.minerals_used_active_forces,
                    vespene_used_active_forces=event.vespene_used_active_forces,
                )
            )
        elif isinstance(event, sc2reader.events.UnitBornEvent):
            if is_worker_unit(event.unit_type_name):
                worker_events.append(
                    WorkerEvent(
                        frame=frame,
                        pid=event.upkeep_pid,
                        is_born=True,
                        unit_type_name=event.unit_type_name,
                    )
                )
        elif isinstance(event, sc2reader.events.UnitDiedEvent):
            unit = getattr(event, "unit", None)
            if unit is not None and is_worker_unit(unit.name):
                owner_pid = getattr(unit, "owner_pid", None)
                if owner_pid is not None:
                    worker_events.append(
                        WorkerEvent(
                            frame=frame,
                            pid=owner_pid,
                            is_born=False,
                            unit_type_name=unit.name,
                        )
                    )

    stats_by_pid: dict[int, list[PlayerStatsAtFrame]] = {}
    for s in stats_events:
        if s.pid not in stats_by_pid:
            stats_by_pid[s.pid] = []
        stats_by_pid[s.pid].append(s)

    for pid in stats_by_pid:
        stats_by_pid[pid].sort(key=lambda x: x.frame)

    worker_events.sort(key=lambda x: x.frame)

    max_gameloop = replay.frames
    tick_count = (max_gameloop // replay_tick) + 1

    timeline: list[list[TimelineDataPoint]] = []

    for tick_idx in range(tick_count):
        target_gameloop = tick_idx * replay_tick
        tick_points: list[TimelineDataPoint] = []

        for idx, pid in enumerate(player_pids):
            state = players[idx]

            for we in worker_events:
                if we.pid == pid and we.frame <= target_gameloop:
                    if we.is_born:
                        state.workers_produced += 1
                    else:
                        state.workers_lost += 1

            stats_list = stats_by_pid.get(pid, [])
            closest_stats: PlayerStatsAtFrame | None = None
            for s in stats_list:
                if s.frame <= target_gameloop:
                    closest_stats = s
                else:
                    break

            if closest_stats:
                state.workers_active = closest_stats.workers_active
                state.total_resources_lost = closest_stats.minerals_lost + closest_stats.vespene_lost
                state.workers_killed = closest_stats.minerals_killed + closest_stats.vespene_killed
                state.total_resources_collected = (
                    closest_stats.minerals_current
                    + closest_stats.vespene_current
                    + closest_stats.minerals_lost
                    + closest_stats.vespene_lost
                )
                supply_block = 1 if closest_stats.food_used >= 0.95 * closest_stats.food_made else 0
                total_army_value = closest_stats.minerals_used_active_forces + closest_stats.vespene_used_active_forces
                collection_rate = closest_stats.minerals_collection_rate + closest_stats.vespene_collection_rate
            else:
                supply_block = 0
                total_army_value = 0
                collection_rate = 0

            seconds = target_gameloop / 22.4
            spm = (state.workers_produced / seconds * 60.0) if seconds > 0 else 0.0

            tick_points.append(
                TimelineDataPoint(
                    gameloop=target_gameloop,
                    workers_active=state.workers_active,
                    workers_produced=state.workers_produced,
                    workers_lost=state.workers_lost,
                    supply=closest_stats.food_used if closest_stats else 0.0,
                    supply_cap=closest_stats.food_made if closest_stats else 0.0,
                    supply_block=supply_block,
                    spm=round(spm, 2),
                    total_army_value=total_army_value,
                    total_resources_lost=state.total_resources_lost,
                    total_resources_collected=state.total_resources_collected,
                    workers_killed=state.workers_killed,
                    resource_collection_rate_all=collection_rate,
                )
            )

        timeline.append(tick_points)

    return players, timeline


@replay_comparer_router.post("/parse_replay")
async def parse_replay_file(
    replay_file: Annotated[UploadFile, File(description="The SC2Replay file to parse")],
    replay_tick: Annotated[str, Form(description="Gameloop tick interval (e.g. 224 for 22.4 seconds)")],
) -> JSONResponse:
    try:
        tick_value = int(replay_tick)
        if tick_value <= 0:
            return JSONResponse({"error": "replay_tick must be positive"}, status_code=400)
    except ValueError:
        return JSONResponse({"error": "replay_tick must be an integer"}, status_code=400)

    try:
        contents = await replay_file.read()
        data = BytesIO(contents)
        players, timeline = parse_replay_timeline(data, tick_value)

        player1 = {"name": players[0].name} if len(players) > 0 else {"name": ""}
        player2 = {"name": players[1].name} if len(players) > 1 else {"name": ""}

        timeline_serialized = [[point.__dict__ for point in tick_points] for tick_points in timeline]

        return JSONResponse(
            {
                "player1": player1,
                "player2": player2,
                "timeline": timeline_serialized,
            }
        )
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": str(e)}, status_code=400)
