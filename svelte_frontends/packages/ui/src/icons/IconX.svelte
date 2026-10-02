<script lang="ts">
// ISC © Lucide contributors — paths from lucide `x` (ISC licensed).
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
    <path d="M18 6 6 18" />
    <path d="m6 6 12 12" />
</svg>
