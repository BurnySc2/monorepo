<script lang="ts">
    export let board = [
        ["X", "O", ""],
        ["", "", ""],
        ["", "", ""],
    ]
    const boardSize = 50
</script>

<!-- <div class="grid grid-cols-3 w-[{boardSize}vh] h-[{boardSize}vh]"> -->
<div class="grid grid-cols-3 w-[{boardSize}vh] ">
    {#each board as row}
        {#each row as cell}
            <span class="p-2 m-2 border-2 border-black">
                <svg>
                    {#if cell == ""}
                        <div />
                    {:else if cell == "X"}
                        <path stroke="#000" stroke-width="12" stroke-linecap="square" d="M 10,10 90,90 M 10,90 90,10" />
                    {:else if cell == "O"}
                        <ellipse
                            xmlns="http://www.w3.org/2000/svg"
                            ry="40.5"
                            rx="40.5"
                            cy="50"
                            cx="50"
                            stroke-opacity="null"
                            stroke-width="8"
                            stroke="#000"
                            fill="#ffffff"
                        />
                    {/if}
                </svg>
            </span>
        {/each}
    {/each}
</div>
