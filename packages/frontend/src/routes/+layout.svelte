<script lang="ts">
	import 'carbon-components-svelte/css/g100.css';
	import '@carbon/charts/styles.css';
	import '../app.css';
	let { children } = $props();
</script>

{@render children()}
