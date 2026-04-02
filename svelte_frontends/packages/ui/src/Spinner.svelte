<script lang="ts">
// Simple spinner component – no props needed
</script>

<style>
.spinner {
    display: inline-block;
    width: 1.5rem;
    height: 1.5rem;
    border: 3px solid rgba(0, 0, 0, 0.2);
    border-top-color: rgba(0, 0, 0, 0.6);
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}
</style>

<div
    class="spinner"
    aria-label="Loading"
></div>
