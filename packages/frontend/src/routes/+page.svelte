<script lang="ts">
	import type { GeomorphData } from '$lib/types/GeomorphData';
	import {
		FileUploaderDropContainer,
		DataTable,
		Pagination,
		Toggle,
		Toolbar,
		ToolbarContent,
		Button,
		InlineLoading,
		ToastNotification,
		Tag
	} from 'carbon-components-svelte';
	import type { DataTableHeader } from 'carbon-components-svelte/src/DataTable/DataTable.svelte';
	import Reset from 'carbon-icons-svelte/lib/Reset.svelte';
	import Download from 'carbon-icons-svelte/lib/Download.svelte';
	import {
		geomorphData,
		chartData,
		uploadAndAnalyzeFile,
		reanalyzeData,
		resetToggles,
		updateToggle
	} from '$lib/store';
	import { onMount, onDestroy } from 'svelte';
	import { Chart, DoughnutController, ArcElement, Tooltip, Legend, Title } from 'chart.js';
	import ChartDataLabels from 'chartjs-plugin-datalabels';

	// Register Chart.js components
	Chart.register(DoughnutController, ArcElement, Tooltip, Legend, Title, ChartDataLabels);

	// Declare variables before any functions use them
	let tableRows: GeomorphData[] = [];
	let chartDataValue: { group: string; value: number }[] = [];
	let chart: Chart | null = null;
	let chartCanvas: HTMLCanvasElement;
	let pageSize = 20;
	let page = 1;
	let isLoading = false;
	let isChartLoading = false;
	let error: Error | null = null;
	let fileUploaded = false;
	let showErrorToast = false;

	// Unsubscribe when component is destroyed
	const unsubGeomorphData = geomorphData.subscribe((value) => {
		tableRows = value;
	});

	// Define a separate update function that doesn't reference chart variable directly
	function safeUpdateChart() {
		if (typeof window !== 'undefined' && chart && chartDataValue.length > 0) {
			updateChart();
		}
	}

	const unsubChartData = chartData.subscribe((value) => {
		chartDataValue = value;
		// Using a separate function to avoid the direct reference to chart
		if (typeof window !== 'undefined') {
			setTimeout(safeUpdateChart, 0);
		}
	});

	// Cleanup subscriptions on component destruction
	onDestroy(() => {
		unsubGeomorphData();
		unsubChartData();
	});

	const headers: DataTableHeader[] = [
		{ key: 'stream', value: 'Stream' },
		{ key: 'ksn', value: 'KSN' },
		{ key: 'theta_chi', value: 'Theta Chi' },
		{ key: 'theta_sa', value: 'Theta SA' },
		{ key: 'rfit_theta_tt', value: 'R-fit Theta TT' },
		{ key: 'rfit_theta_tak', value: 'R-fit Theta TAK' },
		{ key: 'error_tt', value: 'Error TT' },
		{ key: 'error_tak', value: 'Error TAK' },
		{ key: 'interpretable_user', value: 'Interpretable', sort: false },
		{ key: 'channel_type', value: 'Channel Type' }
	];

	// Variables already declared above

	// Convert chartDataValue to Chart.js format and update chart
	function updateChart() {
		// Check for browser environment first
		if (typeof window === 'undefined' || !chart || !chartDataValue.length) return;

		const labels = chartDataValue.map((item) => item.group);
		const data = chartDataValue.map((item) => item.value);
		const backgroundColor = labels.map((label) => {
			if (label === 'Fluvial') return '#0072c3';
			if (label === 'Transitional') return '#da1e28';
			if (label === 'Colluvial') return '#24a148';
			return '#888888'; // Default color
		});

		chart.data.labels = labels;
		chart.data.datasets[0].data = data;
		chart.data.datasets[0].backgroundColor = backgroundColor;
		chart.update();
	}

	// Initialize Chart.js when canvas is available
	function initChart() {
		// Check for browser environment first
		if (typeof window === 'undefined' || !chartCanvas || !chartDataValue.length) return;

		const labels = chartDataValue.map((item) => item.group);
		const data = chartDataValue.map((item) => item.value);
		const backgroundColor = labels.map((label) => {
			if (label === 'Fluvial') return '#0072c3';
			if (label === 'Transitional') return '#da1e28';
			if (label === 'Colluvial') return '#24a148';
			return '#888888'; // Default color
		});

		chart = new Chart(chartCanvas, {
			type: 'doughnut',
			data: {
				labels: labels,
				datasets: [
					{
						data: data,
						backgroundColor: backgroundColor,
						borderWidth: 1
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				animation: {
					duration: 2000 // Longer animation for better export quality
				},
				plugins: {
					datalabels: {
						formatter: (value: number, ctx) => {
							// Calculate percentage - TypeScript safe implementation
							const dataset = ctx.chart.data.datasets[0];
							// Type assertion to ensure we're working with an array of numbers
							const dataArray = dataset.data as number[];
							const dataSum = dataArray.reduce((acc: number, current: number) => acc + current, 0);
							const percentage = ((value * 100) / dataSum).toFixed(1) + '%';
							return percentage;
						},
						color: '#ffffff',
						font: {
							weight: 'bold',
							size: 14
						},
						anchor: 'center',
						align: 'center',
						offset: 0
					},
					title: {
						display: true,
						text: 'Channel Type Distribution',
						color: '#ffffff',
						font: {
							size: 16,
							weight: 'bold'
						}
					},
					legend: {
						position: 'bottom',
						labels: {
							color: '#ffffff',
							font: {
								size: 14
							}
						}
					},
					tooltip: {
						enabled: true,
						backgroundColor: 'rgba(0, 0, 0, 0.7)',
						titleFont: {
							size: 14,
							weight: 'bold'
						},
						bodyFont: {
							size: 13
						},
						padding: 10,
						displayColors: true,
						callbacks: {
							label: function (context) {
								const label = context.label || '';
								const value = (context.raw as number) || 0;

								// Type-safe implementation
								const dataset = context.chart.data.datasets[0];
								const dataArray = dataset.data as number[];
								const dataSum = dataArray.reduce(
									(acc: number, current: number) => acc + current,
									0
								);

								const percentage = ((value * 100) / dataSum).toFixed(1);
								return `${label}: ${value} (${percentage}%)`;
							}
						}
					}
				}
			}
		});
	}

	onMount(() => {
		// onMount only runs in the browser, but adding an extra check doesn't hurt
		if (typeof window !== 'undefined' && chartDataValue.length > 0 && chartCanvas) {
			initChart();
		}
	});

	function handleFileUpload(files: readonly File[]) {
		if (!files || files.length === 0) return;

		isLoading = true;
		error = null;
		showErrorToast = false;

		uploadAndAnalyzeFile(files[0])
			.then(() => {
				isLoading = false;
				fileUploaded = true;
				// Initialize chart after data is loaded (browser-only)
				if (typeof window !== 'undefined') {
					setTimeout(() => {
						if (chartCanvas && !chart && chartDataValue.length > 0) {
							initChart();
						} else if (chart && chartDataValue.length > 0) {
							updateChart();
						}
					}, 0);
				}
			})
			.catch((err) => {
				isLoading = false;
				error = err;
				showErrorToast = true;
				setTimeout(() => {
					showErrorToast = false;
				}, 5000); // Auto-hide toast after 5 seconds
			});
	}

	function handleReanalyze() {
		isChartLoading = true;
		error = null;

		reanalyzeData()
			.then(() => {
				isChartLoading = false;
				// Update chart after reanalysis (browser-only)
				if (typeof window !== 'undefined' && chart && chartDataValue.length > 0) {
					updateChart();
				}
			})
			.catch((err) => {
				isChartLoading = false;
				error = err;
				showErrorToast = true;
				setTimeout(() => {
					showErrorToast = false;
				}, 5000);
			});
	}

	function handlePagination(e: CustomEvent) {
		page = e.detail.page;
		pageSize = e.detail.pageSize;
	}

	function handleToggleChange(rowId: string | number, value: boolean) {
		updateToggle(rowId, value);
	}

	function resetUpload() {
		fileUploaded = false;
		error = null;
		showErrorToast = false;
		// Reset the stores
		resetToggles();
		// Destroy chart instance
		if (chart) {
			chart.destroy();
			chart = null;
		}
	}

	function downloadChartAsPNG() {
		if (!chart || typeof window === 'undefined') return;

		const scaleFactor = 3; // Increase for even sharper images
		const originalCanvas = chart.canvas;

		// Create a temporary canvas
		const tempCanvas = document.createElement('canvas');
		tempCanvas.width = originalCanvas.width * scaleFactor;
		tempCanvas.height = originalCanvas.height * scaleFactor;

		// Append tempCanvas to body to ensure proper rendering
		tempCanvas.style.position = 'absolute';
		tempCanvas.style.left = '-9999px';
		document.body.appendChild(tempCanvas);

		// Copy current chart data and configuration
		const chartData = JSON.parse(JSON.stringify(chart.data));

		// Create a new temporary chart with the same data but higher resolution
		const tempChart = new Chart(tempCanvas, {
			type: 'doughnut',
			data: chartData,
			options: {
				animation: false,
				responsive: false,
				maintainAspectRatio: false,
				devicePixelRatio: scaleFactor,
				plugins: {
					datalabels: {
						formatter: (value: number, ctx) => {
							// Type-safe implementation
							const dataset = ctx.chart.data.datasets[0];
							const dataArray = dataset.data as number[];
							const dataSum = dataArray.reduce((acc: number, current: number) => acc + current, 0);

							const percentage = ((value * 100) / dataSum).toFixed(1) + '%';
							return percentage;
						},
						color: '#ffffff', // Black labels for export
						font: {
							weight: 'bold',
							size: 14 * scaleFactor
						},
						anchor: 'center',
						align: 'center',
						offset: 0
					},
					title: {
						display: true,
						text: 'Channel Type Distribution',
						color: '#000000', // Use black text for export
						font: {
							size: 16 * scaleFactor,
							weight: 'bold'
						}
					},
					legend: {
						position: 'bottom',
						labels: {
							color: '#000000', // Use black text for export
							font: {
								size: 14 * scaleFactor
							}
						}
					},
					tooltip: {
						enabled: false // Disable tooltip for export
					}
				}
			}
		});

		// Wait for chart to render properly (increase timeout if needed)
		setTimeout(() => {
			try {
				// Download the PNG
				const dataURL = tempCanvas.toDataURL('image/png', 1.0);
				const link = document.createElement('a');
				link.download = 'channel-type-distribution.png';
				link.href = dataURL;
				document.body.appendChild(link);
				link.click();
				document.body.removeChild(link);
			} catch (e) {
				console.error('Error exporting chart:', e);
			} finally {
				// Clean up
				tempChart.destroy();
				document.body.removeChild(tempCanvas);
			}
		}, 500); // Adjust timeout as needed
	}
</script>

<div class="flex min-h-screen w-full flex-col items-center justify-center p-4">
	{#if showErrorToast && error}
		<div class="fixed right-4 top-4 z-50">
			<ToastNotification
				kind="error"
				title="Error"
				subtitle={error.message}
				caption="Please try again"
				timeout={5000}
				on:close={() => (showErrorToast = false)}
			/>
		</div>
	{/if}

	{#if !fileUploaded}
		<div class="w-full max-w-2xl rounded-lg border border-gray-200 p-8 shadow-sm">
			<h2 class="!mb-6 text-center text-xl font-semibold">Yuta</h2>

			{#if isLoading}
				<div class="flex flex-col items-center justify-center space-y-4 py-8">
					<InlineLoading description="Analyzing file..." status="active" />
				</div>
			{:else}
				<div class="flex w-full justify-center">
					<FileUploaderDropContainer
						labelText="Drag and drop a MAT file here or click to upload"
						validateFiles={(files) => {
							return files.filter((file) => file.name.endsWith('.mat'));
						}}
						on:change={(e) => {
							handleFileUpload(e.detail);
						}}
						class="center flex w-full justify-center"
					/>
				</div>
			{/if}
		</div>
	{:else if tableRows.length > 0}
		<div class="w-full max-w-7xl">
			<div class="!my-8 flex items-center justify-between">
				<h1 class="text-2xl font-bold">Yuta</h1>
				<Button kind="tertiary" on:click={resetUpload}>Upload New File</Button>
			</div>

			<div class="!mb-12">
				<DataTable
					title="Stream Analysis"
					description="Geomorphological data analysis"
					{headers}
					rows={tableRows}
					{pageSize}
					{page}
					size="compact"
					sortable
				>
					<Toolbar>
						<ToolbarContent>
							<Button
								kind="secondary"
								icon={Reset}
								iconDescription="Reset"
								on:click={() => resetToggles()}
							/>
							<Button on:click={() => handleReanalyze()} disabled={isChartLoading}>
								{#if isChartLoading}
									<InlineLoading description="Reanalyzing..." status="active" />
								{:else}
									Reanalyze
								{/if}
							</Button>
						</ToolbarContent>
					</Toolbar>
					<svelte:fragment slot="cell" let:row let:cell>
						{#if cell.key === 'interpretable_user'}
							<div class="flex items-center justify-center">
								<Toggle
									toggled={row.interpretable_user}
									on:toggle={(e) => {
										handleToggleChange(row.id, e.detail.toggled);
									}}
									size="sm"
									hideLabel
								>
									<span slot="labelA" class="hidden">No</span>
									<span slot="labelB" class="hidden">Yes</span>
								</Toggle>
							</div>
						{:else if cell.key === 'channel_type'}
							<div class="flex items-center justify-center">
								{#if cell.value === 'fluvial'}
									<Tag type="cyan" size="sm">fluvial</Tag>
								{:else if cell.value === 'transitional'}
									<Tag type="red" size="sm">transitional</Tag>
								{:else if cell.value === 'colluvial'}
									<Tag type="green" size="sm">colluvial</Tag>
								{:else}
									{cell.value}
								{/if}
							</div>
						{:else}
							{cell.value}
						{/if}
					</svelte:fragment>
				</DataTable>
				<Pagination
					totalItems={tableRows.length}
					pageSizes={[10, 20, 30, 40, 50]}
					{pageSize}
					{page}
					on:update={handlePagination}
				/>
			</div>

			<div class="!mb-12">
				{#if chartDataValue.length > 0}
					<div class="w-full rounded-lg border border-gray-200 p-4">
						<div class="mb-2 flex justify-end space-x-2">
							<Button
								kind="secondary"
								icon={Download}
								iconDescription="Download as PNG"
								on:click={downloadChartAsPNG}
							/>
						</div>
						<div class="h-96">
							<canvas bind:this={chartCanvas}></canvas>
						</div>
					</div>
				{:else}
					<div class="rounded-lg bg-yellow-50 p-4 text-yellow-700">
						<p>No distribution data available.</p>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
