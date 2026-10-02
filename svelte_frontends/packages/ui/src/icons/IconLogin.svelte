<script lang="ts">
// ISC © Lucide contributors — paths from lucide `log-in` (ISC licensed).
interface Props {
    class?: string
    size?: number
}
let { class: class_name = "", size = 24 }: Props = $props()
</script>

<svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    class={class_name}
    aria-hidden="true"
>
    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
    <path d="M10 17l5-5-5-5" />
    <path d="M15 12H3" />
</svg>
