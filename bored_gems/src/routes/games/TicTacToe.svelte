<script lang="ts">
    import { onMount } from "svelte"

    // Get game id from url ?gameid=1234
    let gameId = 1234

    // Figure out if logged in user is player 1 or player 2
    let playerType: "player1" | "player2" | null = "player1"
    const getCurrentGameState = () => {
        // grab data from db
    }
    const onDbChange = () => {
        // hook that is launched when data in db changes, e.g. when opponent player makes move
        // if all positions are used: end game, calculate outcome
    }
    const onClick = (cell: any) => {
        // when cell is clicked, apply the move in the db
    }
    onMount(() => {
        // on page load, set playerType and get current game state
    })
</script>

<!-- TODO make 3x3 game field with onClick handler -->
<div>hello world</div>
