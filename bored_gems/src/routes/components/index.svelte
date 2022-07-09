<!-- TODO dont show these pages on production -->
<script lang="ts">
    // A path to preview all components
    let components = [
        {
            name: "TicTacToe",
            link: "components/tictactoe",
        },
        {
            name: "Lobbies Row",
            link: "components/lobbiesrow",
        },
        {
            name: "Create lobby",
            link: "components/createlobby",
        },
    ]
</script>

<div class="flex flex-col items-center justify-center h-screen">
    {#each components as component}
        <a class="bg-blue-400 hover:bg-blue-300 p-1 m-1 border-2 border-black " href={component.link}
            >{component.name}</a
        >
    {/each}
</div>
