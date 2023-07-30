<header>
    <div>
        <!-- https://kit.svelte.dev/docs/link-options#data-sveltekit-preload-data -->
        <a id="ffmpegcrf" data-sveltekit-preload-data="hover" href="/ffmpeg/crf">CRF</a>
        <a id="ffmpegaddsubs" data-sveltekit-preload-data="hover" href="/ffmpeg/addsubs">Add subs</a>
        <a id="ffmpegburnsubs" data-sveltekit-preload-data="hover" href="/ffmpeg/burnsubs">Burn subs</a>
    </div>
</header>
<slot />

<style>
    div {
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;
    }
    a {
        margin: 0.5rem;
        padding: 0.5rem;
        border-radius: 0.5rem;
        border: 1px solid black;
    }
</style>
