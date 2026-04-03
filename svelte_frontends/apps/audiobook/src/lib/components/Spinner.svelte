<script lang="ts">
interface Props {
    size?: "sm" | "md" | "lg"
    color?: string
}

let { size = "md", color = "border-blue-500" }: Props = $props()

const sizeClasses: Record<string, string> = {
    sm: "w-5 h-5 border-2",
    md: "w-10 h-10 border-4",
    lg: "w-16 h-16 border-4",
}
</script>

<div
    class="{sizeClasses[size]} {color} border-t-transparent rounded-full animate-spin mx-auto"
    role="status"
    aria-label="Loading"
></div>

<style>
@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

.animate-spin {
    animation: spin 1s linear infinite;
}
</style>
