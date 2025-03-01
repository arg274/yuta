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
	import { DonutChart } from '@carbon/charts-svelte';
	import Reset from 'carbon-icons-svelte/lib/Reset.svelte';
	import {
		geomorphData,
		chartData,
		uploadAndAnalyzeFile,
		reanalyzeData,
		resetToggles,
		updateToggle
	} from '$lib/store';

	// Subscribe to the stores
	let tableRows: GeomorphData[] = [];
	let chartDataValue: { group: string; value: number }[] = [];

	// Unsubscribe when component is destroyed
	const unsubGeomorphData = geomorphData.subscribe((value) => {
		tableRows = value;
	});

	const unsubChartData = chartData.subscribe((value) => {
		chartDataValue = value;
	});

	// Cleanup subscriptions on component destruction
	import { onDestroy } from 'svelte';
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

	let pageSize = 20;
	let page = 1;
	let isLoading = false;
	let isChartLoading = false;
	let error: Error | null = null;
	let fileUploaded = false;
	let showErrorToast = false;

	let chartOptions = {
		title: 'Channel Type Distribution',
		resizable: true,
		donut: {
			alignment: 'center'
		},
		height: '400px',
		theme: 'g100', // Carbon dark theme
		color: {
			scale: {
				Fluvial: '#0072c3', // cyan (Carbon cyan-60)
				Transitional: '#da1e28', // red (Carbon red-60)
				Colluvial: '#24a148' // green (Carbon green-60)
			}
		},
		data: {
			groupMapsTo: 'group', // Ensure this matches your data structure
			loading: isChartLoading // Use built-in loading state
		}
	};

	function handleFileUpload(files: readonly File[]) {
		if (!files || files.length === 0) return;

		isLoading = true;
		error = null;
		showErrorToast = false;

		uploadAndAnalyzeFile(files[0])
			.then(() => {
				isLoading = false;
				fileUploaded = true;
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
						class="center flex  w-full justify-center"
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
					<div class="h-96 w-full rounded-lg border border-gray-200 p-4">
						<DonutChart data={chartDataValue} options={chartOptions} />
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
