<script lang="ts">
    import { loginUser, supabase } from "../../supabase"

    let email = ""
    let password = ""

    const loginHandler = async () => {
        // VERIFY INPUT DATA
        // SANITISE INPUT DATA
        console.log("Logging in...")
        await loginUser(email, password, "/")
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
