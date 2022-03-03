<script lang="ts">
    const raceIcons = {
        T: "https://spire.gg/static/games/SC2/race_TERRAN.svg",
        Z: "https://spire.gg/static/games/SC2/race_ZERG.svg",
        P: "https://spire.gg/static/games/SC2/race_PROTOSS.svg",
        R: "https://spire.gg/static/games/SC2/race_RANDOM.svg",
    }
    export let playerId = 123
    export let avatar = "https://dp8bnrj9moj7v.cloudfront.net/2f0fb61d-0e14-4c34-a89b-1460fe7c36fb"
    export let race = "T"
    export let raceIcon = raceIcons[race]
    export let name = "MonstR"
</script>

<a class="flex col-span-5 items-center hover:bg-gray-500" href={`http://www.players.com/${playerId}`}>
    <img src={avatar} alt="avatar" class="h-10" />
    <img src={raceIcon} alt="race" class="h-10" />
    <div class="text-right">{name}</div>
</a>
