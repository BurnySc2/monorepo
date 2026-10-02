<script lang="ts">
// ISC © Lucide contributors — paths from lucide `list-plus` (ISC licensed).
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
    <path d="M16 5H3" />
    <path d="M11 12H3" />
    <path d="M16 19H3" />
    <path d="M18 9v6" />
    <path d="M21 12h-6" />
</svg>
