<script lang="ts">
    export let joinLobbyShown = true

    const joinLobby = () => {
        console.log("joining lobby")
        joinLobbyShown = false
    }
</script>

<div class="flex items-center justify-center absolute z-40 w-screen h-screen">
    <!-- bg-opacity-70  -->
    <div
        class="flex items-center justify-center min-w-[40vw] min-h-[40vh] bg-white backdrop-blur-sm bg-white/5 border-8 rounded border-green-400"
    >
        custom username lobby password Cancel Join
    </div>
    <button on:click={joinLobby}>HELLOOOOOOOOOOOOOOOOOO</button>
</div>
