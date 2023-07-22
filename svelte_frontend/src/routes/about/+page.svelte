<script lang="ts">
    // https://youtu.be/iX_QyjdctsQ
    export let defaultText = "this text"
    let someText = defaultText
</script>

<div>
    <section>
        <h1 class="text-center my-2">
            This is my about page! Here I display features of svelte that I have implemented (= copied)
        </h1>
    </section>
    <section>
        <button
            id="mybutton"
            class="p-1 border-2"
            on:click={() => {
                someText = someText === defaultText ? "is changing" : defaultText
            }}
        >
            Click me: {someText}
        </button>
    </section>
    <section>
        <!-- modal https://youtu.be/q1fsBWLpYW4?t=45 -->
        <dialog id="d">
            <form method="dialog">
                <p>Hi Mom! Check out my dialog</p>
                <button>Close via form</button>
            </form>
            <button onclick="d.close()">Close via button</button>
        </dialog>
        <button onclick="d.showModal()">Open Dialog</button>
    </section>
    <section>
        <button popovertarget="expandstuff">Expand via popover</button>
        <div id="expandstuff" popover>
            <p>Amazing new content</p>
        </div>
    </section>
    <section>
        <!-- https://www.youtube.com/watch?v=iX_QyjdctsQ -->
        <form>
            <fieldset>
                <legend>Some Topic</legend>
                <div>
                    <label
                        >Color
                        <input type="text" list="color-list" />
                    </label>
                    <datalist id="color-list">
                        <option value="Red" />
                        <option value="Green" />
                        <option value="Blue" />
                    </datalist>
                </div>
                <div>
                    <progress value="50" max="100">50%</progress>
                </div>
            </fieldset>
        </form>
    </section>
</div>

<style>
    dialog::backdrop {
        background-color: rgba(0, 0, 255, 0.2);
    }
    section > button {
        border: 1px solid black;
        border-radius: 5px;
        margin: 1rem;
        padding: 1rem;
    }
    section > dialog {
        border: 1px solid black;
        border-radius: 5px;
        padding: 1rem;
    }
</style>
