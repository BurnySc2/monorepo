<script lang="ts">
    // TODO add type
    import TournamentGroup from "./TournamentGroup.svelte"

    export let groups = []
</script>

<div class="m-8">
    <div class="flex flex-col m-2">
        <div>Round of 16</div>
        <div>Format: Best of 3</div>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3">
        {#each groups as { groupId, groupName, participants }}
            <TournamentGroup {groupId} {groupName} {participants} />
        {/each}
    </div>
</div>
