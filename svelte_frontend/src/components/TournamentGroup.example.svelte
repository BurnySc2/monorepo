<script lang="ts">
    import TournamentGroup from "./TournamentGroup.svelte"

    // Group id might be needed for fetching group score
    let groupId = 1234
    let groupName = 'Group "A"'
    let participants = [
        {
            rank: 1,
            playerId: 321,
            name: "MonstR",
            matches: 3,
            wins: 3,
            losses: 0,
            mapWins: 6,
            mapLosses: 1,
            totalScore: "+5",
        },
        {
            rank: 2,
            playerId: 322,
            name: "Iba",
            matches: 3,
            wins: 2,
            losses: 1,
            mapWins: 4,
            mapLosses: 2,
            totalScore: "+2",
        },
        {
            rank: 3,
            playerId: 323,
            name: "Neuling",
            matches: 3,
            wins: 1,
            losses: 2,
            mapWins: 3,
            mapLosses: 4,
            totalScore: "-1",
        },
        {
            rank: 4,
            playerId: 324,
            name: "TerribleOne",
            matches: 3,
            wins: 0,
            losses: 3,
            mapWins: 0,
            mapLosses: 6,
            totalScore: "-6",
        },
    ]
</script>

<TournamentGroup {groupId} {groupName} {participants} />
