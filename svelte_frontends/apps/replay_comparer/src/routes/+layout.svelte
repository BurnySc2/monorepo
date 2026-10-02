<script lang="ts">
import "@repo/ui/styles.css"
import { Navigation } from "@repo/ui"

let { children } = $props()
</script>

<Navigation currentApp="Replay Comparer" />

{@render children?.()}
