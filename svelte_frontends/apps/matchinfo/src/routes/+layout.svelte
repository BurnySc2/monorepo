<script lang="ts">
import "@repo/ui/styles.css"

let { children } = $props()
</script>

<div class="min-h-screen bg-gray-900 text-white p-8">{@render children()}</div>
