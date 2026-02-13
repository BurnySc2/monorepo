"""
TODO
Allow all users to upload a replay which will be parsed and the replays will be compared

Allow only logged in users to save their uploaded replay as "target" replay (which has the best benchmarks)
- Give a replay a name/label/build order name
- Save replay in minio
- Save Minio object name in db, connect with twitch user name

Plot stats for both replays in graph
- Worker count
- CC/Nexus idle time
- Time supply blocked
- Army value

Compare for (table, mark green for better, red for worse)
(Allow user to save their settings as cookies?)
- Time of nth tank train-ordered (or completed, can you track that?)
- Time of upgrade started/completed
- Time of nth townhall started


Routes:
index.html
- Show 2 sides
    - Drop target replay here (only allow 1 file)
    - Drop real replays here (allow >=1 files)
    - When both drop zones have files in them, run comparison with
        - 1 goal replay
        - >=1 real replays
compared_replays.html
- Display timings and graphs
    - Allow adding timings
        - Dropdown menu (nth unit type produced, nth upgrade started, n worker count reached,
        n supply reached, n army supply reached), save to cookies
    - Allow removing timings, save to cookies
    - Select graph (backend rendering after selecting another?)
- Have hidden input field (with compressed replay data) that will send data to backend to render it?
- Drop replay to change the target-replay
- Drop replay to add to comparison (add new parsed replay at top?)
"""
