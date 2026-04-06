<script lang="ts">
import "@repo/ui/styles.css"
import { Spinner } from "@repo/ui"

let { children } = $props()
</script>

<div class="min-h-screen bg-gray-900 text-white p-8">
    <Spinner />
    {@render children()}
</div>
