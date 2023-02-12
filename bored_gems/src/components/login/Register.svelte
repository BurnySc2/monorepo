<script lang="ts">
    import { registerUser, supabase, supabaseUsernameTable } from "../../supabase"

    let email = ""
    let username = ""
    let password = ""

    const registerHandler = async () => {
        // VERIFY INPUT DATA
        // SANITISE INPUT DATA
        console.log("Registering...")
        await registerUser(email, username, password, "/")
    }
</script>

<div class="flex flex-col items-center justify-center h-screen">
    <div class="flex flex-col min-w-[50vw] min-h-[50vh] border-2 border-black space-y-2">
        <div class="grid grid-cols-1">
            <div>Email</div>
            <input type="email" bind:value={email} />
            <div>Username</div>
            <input type="text" bind:value={username} />
            <div>Password</div>
            <input type="password" bind:value={password} />
        </div>
    </div>
    <div class="flex gap-x-2">
        <button on:click={registerHandler} class="hover:bg-green-500 p-2">Register</button>
        <a href="/" class="hover:bg-red-500 p-2">Back</a>
    </div>
</div>
