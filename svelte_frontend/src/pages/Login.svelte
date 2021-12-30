<script lang="ts">
    import Inputfield from "../components/Inputfield.svelte"
    import Button from "../components/Button.svelte"
    import { request, gql } from "graphql-request"

    let loginEmail = "asd"
    let loginPassword = "asd"

    let registerUsername = "asd"
    let registerEmail = "asd"
    let registerPassword = "asd"
    let registerPasswordRepeated = "asd"

    let resetEmail = "asd"

    const ip = process.env.BACKEND_SERVER || "localhost:8000"
    const GRAPHQL_ENDPOINT = `http://${ip}/graphql`

    let loginSubmit = async () => {
        let loginQuery = gql`
            query LoginQuery($email: String!, $password: String!) {
                userLogin(email: $email, password: $password)
            }
        `
        let variables = {
            email: loginEmail,
            password: loginPassword,
        }
        const data = await request(GRAPHQL_ENDPOINT, loginQuery, variables)
        // TODO set login cookie if login successful
        console.log("Do login submit request")
    }
    let registerSubmit = async () => {
        let registerQuery = gql`
            mutation RegisterMutation($username: String!, $email: String!, $password: String!, $passwordRepeated: String!) {
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
        const data = await request(GRAPHQL_ENDPOINT, registerQuery, variables)
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
</div>
