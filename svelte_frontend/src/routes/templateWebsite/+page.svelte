<script lang="ts">
    import { onMount } from "svelte"

    // Site layout according to https://youtu.be/bOUhq46fd5g
    export let width = 0
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
            <aside>
                <p>Some extra info</p>
            </aside>
            <p>
                Lorem ipsum dolor sit amet consectetur adipisicing elit. Dicta qui tempora voluptas ea voluptatem? Quasi
                corporis nulla iusto, qui vero minima quam voluptatum natus rerum molestias omnis dolores aliquid
                necessitatibus dolorum saepe nobis aut error itaque consequuntur? Quam quasi animi numquam doloribus
                ipsam, ad error, minima iusto perspiciatis ea perferendis!
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
    aside {
        width: 40%;
        padding-left: 0.5rem;
        margin-left: 0.5rem;
        float: right;
        box-shadow: inset 5px 0 5px -5px #29627e;
        font-style: italic;
        color: #29627e;
        background-color: lightgray;
    }
    aside > p {
        margin: 0.5rem;
    }
</style>
