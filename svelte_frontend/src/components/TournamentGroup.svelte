<script lang="ts">
    import TournamentProfileCard from "./TournamentProfileCard.svelte"

    // Group id might be needed for fetching group score
    export let groupId = 1337
    export let groupName = "Enter group name here"
    type Participant = {
        rank: number
        playerId: number
        name: string
        matches: number
        wins: number
        losses: number
        mapWins: number
        mapLosses: number
        totalScore: string
    }
    export let participants: Participant[] = []
</script>

<div class="m-2">
    <div class="grid grid-cols-12">
        <div class="col-span-6">{groupName}</div>
        <div>M</div>
        <div>W</div>
        <div>L</div>
        <div>S+</div>
        <div>S-</div>
        <div>SD</div>
    </div>
    <div class="grid grid-cols-12 border-2 bg-gray-400 p-1 gap-1 items-center">
        {#each participants as { rank, playerId, name, matches, wins, losses, mapWins, mapLosses, totalScore }}
            <div>{rank}</div>
            <TournamentProfileCard {playerId} {name} />
            <div>{matches}</div>
            <div>{wins}</div>
            <div>{losses}</div>
            <div>{mapWins}</div>
            <div>{mapLosses}</div>
            <div>{totalScore}</div>
        {/each}
    </div>
</div>
