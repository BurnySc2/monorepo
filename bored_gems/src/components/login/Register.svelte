<script lang="ts">
    import { supabase, supabaseUsernameTable } from "../../supabase"

    let email = ""
    let username = ""
    let password = ""

    const registerHandler = async () => {
        // VERIFY INPUT DATA
        // SANITISE INPUT DATA
        console.log(email) // TODO REMOVE ME
        console.log(username) // TODO REMOVE ME
        console.log(password) // TODO REMOVE ME

        const { error } = await supabase.auth.signUp({
            email: email,
            password: password,
        })
        if (error !== null) {
            // TODO error handling, couldnt sign up, dont redirect
            console.log(error)
            return
        }
        // No error

        // Connect username with user account (foreignkey = email)
        await supabaseUsernameTable.insert([
            {
                username: username,
                email: email,
            },
        ])

        // Redirect to root page
        window.location.href = "/"
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
