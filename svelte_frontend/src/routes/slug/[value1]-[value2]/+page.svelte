<script lang="ts">
    import { page } from "$app/stores"

    let value1 = $page.params.value1
    let value2 = $page.params.value2
</script>

<div>
    Hi! You are on page "/slug/{value1}-{value2}"
</div>
