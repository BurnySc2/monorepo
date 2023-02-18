<script lang="ts">
    import { supabase, supabaseUsernameTable, getSupabaseUserFromSession, getUsernameOfUser } from "../supabase"

    import { onMount } from "svelte"
    import type { AuthSession, User } from "@supabase/supabase-js"

    let user: User | null = null
    let email = ""
    let username = ""

    onMount(async () => {
        // Use localstorage to grab the supabase user
        user = await getSupabaseUserFromSession()
        if (!user) {
            // User is not logged in
            return
        }
        // User is logged in
        email = user?.email || ""
        console.log(email) // TODO REMOVE ME

        const responseUsername = await getUsernameOfUser(user)
        if (responseUsername) {
            username = responseUsername
        }
    })

    const resetVariables = () => {
        user = null
        email = ""
        username = ""
    }

    const logoutHandler = async () => {
        await supabase.auth.signOut()
        resetVariables()
    }
</script>

<div class="flex flex-col items-center justify-center h-screen">
    {#if user === null}
        <div>You are not logged in</div>
        <a href="/login" class="border-2 border-black p-2 text-2xl hover:bg-green-500">Login here</a>
        <a href="/register" class="border-2 border-black p-2 text-2xl hover:bg-green-500">Or create an account here</a>
    {:else}
        <a href="/lobbies" class="border-2 border-black p-2 text-2xl hover:bg-green-500">Go to lobbies</a>
        <div>You are logged in as "{email}" with username "{username}"</div>
        <button class="border-2 border-black p-2 text-2xl hover:bg-red-500" on:click={logoutHandler}>Logout</button>
    {/if}
</div>
