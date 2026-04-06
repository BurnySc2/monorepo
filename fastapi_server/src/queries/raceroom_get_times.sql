SELECT
    bt.best_time,
    bt.datetime_driven,
    bt.car_name,
    bt.driving_model,
    p.player_name,
    t.track_name
FROM litestar_rrre_best_time AS bt
INNER JOIN litestar_rrre_player AS p ON bt.player_id = p.player_id
INNER JOIN litestar_rrre_track AS t ON bt.track_id = t.track_id
WHERE
    bt.track_id = COALESCE({ }, bt.track_id)
    AND bt.datetime_driven >= COALESCE({ }, bt.datetime_driven)
    AND bt.datetime_driven <= COALESCE({ }, bt.datetime_driven)
ORDER BY bt.datetime_driven ASC
