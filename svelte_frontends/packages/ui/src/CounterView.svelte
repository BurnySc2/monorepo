<script lang="ts">
import { new_counter } from "./counter.svelte"

let _counter = new_counter()
</script>

<button onclick={() => _counter.decrement()}>-</button>
Current count: {_counter.count}

<button onclick={() => _counter.increment()}>+</button>
