<script lang="ts">
    import { page } from "$app/stores"

    import Headers from "../../components/Headers.svelte"

    let value1 = "-1"
    let value2 = "-1"

    page.subscribe(({ params }) => {
        value1 = params.somevalue1
        value1 = params.someothervalue2
    })
</script>

<Headers />
<div>
    Hi! You are on page "/todo/{value1}-{value2}"
</div>
