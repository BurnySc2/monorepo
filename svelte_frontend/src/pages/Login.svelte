<script lang="ts">
    import Inputfield from "../components/Inputfield.svelte"
    import Button from "../components/Button.svelte"
    import { gql } from "graphql-request"
    import { GRAPHQL_CLIENT, LOGIN_ENDPOINT } from "../functions/constants"
    import { toast, SvelteToast } from "@zerodevx/svelte-toast"

    let loginEmail = "asd"
    let loginPassword = "asd"

    let registerUsername = "asd"
    let registerEmail = "asd"
    let registerPassword = "asd"
    let registerPasswordRepeated = "asd"

    let resetEmail = "asd"

    let loginSubmit = async () => {
        try {
            // eslint-disable-next-line no-undef
            const requestOptions: RequestInit = {
                method: "POST",
                // Allow cookies to be set?
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    email: loginEmail,
                    password: loginPassword,
                }),
            }
            // TODO Handle error: login unsuccessful etc
            let response = await fetch(LOGIN_ENDPOINT, requestOptions)
            if (response.ok) {
                let _data = await response.json()
                // https://github.com/zerodevx/svelte-toast
                toast.push("Login successful!", {
                    theme: {
                        "--toastBackground": "#48BB78",
                        "--toastBarBackground": "#2F855A",
                    },
                })
            }
        } catch {
            // Catch error, server offline etc
        }
    }
    let registerSubmit = async () => {
        let registerQuery = gql`
            mutation RegisterMutation(
                $username: String!
                $email: String!
                $password: String!
                $passwordRepeated: String!
            ) {
                userRegister(
                    username: $username
                    email: $email
                    password: $password
                    passwordRepeated: $passwordRepeated
                )
            }
        `
        let variables = {
            username: registerUsername,
            email: registerEmail,
            password: registerPassword,
            passwordRepeated: registerPasswordRepeated,
        }
        const data = await GRAPHQL_CLIENT.request(registerQuery, variables)
        if (data.userRegister) {
            // https://github.com/zerodevx/svelte-toast
            toast.push("Registration successful!", {
                theme: {
                    "--toastBackground": "#48BB78",
                    "--toastBarBackground": "#2F855A",
                },
            })
        }
        // TODO redirect to new screen if successfully registered
        console.log("Do register submit request")
    }
    let resetSubmit = async () => {
        // TODO write gql query, notify that reset was successful
        console.log("Do reset password submit request")
    }
</script>

<div class="flex">
    <div class="flex-column">
        <div>LOGIN</div>
        <Inputfield descriptionText="Email" inputType="email" bind:bindVariable={loginEmail} />
        <Inputfield descriptionText="Password" inputType="password" bind:bindVariable={loginPassword} />
        <Button buttonText="Login" onClickFunction={loginSubmit} />
    </div>
    <div>
        <div>REGISTER</div>
        <Inputfield descriptionText="Username" bind:bindVariable={registerUsername} />
        <Inputfield descriptionText="Email" inputType="email" bind:bindVariable={registerEmail} />
        <Inputfield descriptionText="Password" inputType="password" bind:bindVariable={registerPassword} />
        <Inputfield
            descriptionText="Password Repeated"
            inputType="password"
            bind:bindVariable={registerPasswordRepeated}
        />
        <Button buttonText="Register" onClickFunction={registerSubmit} />
    </div>
    <div>
        <div>RESET PASSWORD</div>
        <Inputfield descriptionText="Email" inputType="email" bind:bindVariable={resetEmail} />
        <Button buttonText="Reset Password" onClickFunction={resetSubmit} />
    </div>
    <SvelteToast />
</div>
