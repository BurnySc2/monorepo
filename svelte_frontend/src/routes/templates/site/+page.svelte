<script lang="ts">
    import { onMount } from "svelte"

    // Site layout according to https://youtu.be/bOUhq46fd5g
    let width = 0
    $: imgUrl = `https://picsum.photos/${width}/100`
    function setWidth() {
        width = window.innerWidth
    }
    onMount(() => {
        setWidth()
        window.addEventListener("resize", setWidth)
    })
</script>

<head>
    <title>Site</title>
</head>
<body>
    <header>
        {#if width !== 0}
            <img src={imgUrl} alt="" />
        {/if}
        <nav>
            <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/about">About</a></li>
                <li><a href="/browserstorage">BrowserStorage</a></li>
            </ul>
        </nav>
    </header>
    <main>
        <section>
            <h2>Benefits</h2>
            <p>Lorem ipsum dolor sit amet consectetur adipisicing elit. Obcaecati, dolore.</p>
        </section>
        <section>
            <h2>How it works</h2>
            <p>
                Lorem ipsum dolor sit amet consectetur adipisicing elit. Minima consequatur, eum ducimus molestiae odio
                voluptate dolorem sit? A, vel aliquam!
            </p>
        </section>
    </main>

    <footer>
        <ul>
            <li><a href="/">Impressum</a></li>
            <li><a href="/about">Github</a></li>
            <li><a href="/browserstorage">Twitter</a></li>
        </ul>
    </footer>
</body>

<style>
    nav > ul {
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;
        padding: 1rem;
        background-color: #eee;
    }
    nav > ul > li {
        margin: 1rem;
    }
    main > section {
        padding: 1rem;
    }
    footer > ul {
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;
        padding: 1rem;
        background-color: #eee;
    }
    footer > ul > li {
        margin: 1rem;
    }
    li {
        list-style: none;
    }
</style>
