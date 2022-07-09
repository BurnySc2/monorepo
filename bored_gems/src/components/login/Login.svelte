<script lang="ts">
    import { supabase } from "../../supabase"

    let email = ""
    let password = ""

    const loginHandler = async () => {
        // VERIFY INPUT DATA
        // SANITISE INPUT DATA
        console.log(email) // TODO REMOVE ME
        console.log(password) // TODO REMOVE ME

        const { user, session, error } = await supabase.auth.signIn({
            email: email,
            password: password,
        })
        console.log(user) // TODO REMOVE ME
        console.log(session) // TODO REMOVE ME
        if (error !== null) {
            // TODO error handling, couldnt sign up, dont redirect
            console.log(error)
            return
        }
        // No error, redirect to root page
        window.location.href = "/"
    }
</script>

<div class="flex flex-col items-center justify-center h-screen">
    <div class="flex flex-col min-w-[50vw] min-h-[50vh] border-2 border-black space-y-2">
        <div class="grid grid-cols-1">
            <div>Email</div>
            <input type="email" bind:value={email} />
            <div>Password</div>
            <input type="password" bind:value={password} />
        </div>
    </div>
    <div class="flex gap-x-2">
        <button on:click={loginHandler} class="hover:bg-green-500 p-2">Login</button>
        <a href="/" class="hover:bg-red-500 p-2">Back</a>
    </div>
</div>
