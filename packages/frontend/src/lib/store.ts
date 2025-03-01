import { writable } from 'svelte/store';
import type { GeomorphData } from '$lib/types/GeomorphData';
import type { GeomorphResponse } from '$lib/types/GeomorphResponse';

// Create the main store for geomorphological data
export const geomorphData = writable<GeomorphData[]>([]);

// Create additional stores for related data
export const chartData = writable<{ group: string; value: number }[]>([]);

// Function to process and update data
export function processAndUpdateData(response: GeomorphResponse) {
	if (response && response.data && Array.isArray(response.data) && response.data.length > 0) {
		// Update chart data if available
		if (response.graph_data && response.graph_data.dist) {
			const newChartData = Object.entries(response.graph_data.dist).map(([channelType, value]) => ({
				group: channelType.charAt(0).toUpperCase() + channelType.slice(1),
				value: Number(((value as number) * 100).toFixed(1)) // Convert to percentage with 1 decimal place
			}));
			chartData.set(newChartData);
		}

		// Process and round the numerical data
		const processedData = response.data.map((row) => {
			const roundedRow = { ...row };
			roundedRow.ksn = Number(roundedRow.ksn.toFixed(4));
			roundedRow.theta_chi = Number(roundedRow.theta_chi.toFixed(4));
			roundedRow.theta_sa = Number(roundedRow.theta_sa.toFixed(4));
			roundedRow.rfit_theta_tt = Number(roundedRow.rfit_theta_tt.toFixed(4));
			roundedRow.error_tt = Number(roundedRow.error_tt.toFixed(4));
			roundedRow.rfit_theta_tak = Number(roundedRow.rfit_theta_tak.toFixed(4));
			roundedRow.error_tak = Number(roundedRow.error_tak.toFixed(4));

			// Set user interpretable value initially to match original interpretable value
			if (roundedRow.interpretable_user === undefined) {
				roundedRow.interpretable_user = roundedRow.interpretable;
			}

			return roundedRow;
		});

		// Update the store with processed data
		geomorphData.set(processedData);
	}
}

// Function to handle file upload and analysis - now using our server endpoint
export async function uploadAndAnalyzeFile(file: File): Promise<GeomorphData[]> {
	const formData = new FormData();
	formData.append('file', file);

	try {
		// Call our server endpoint instead of the external API directly
		const response = await fetch('/api/analyze', {
			method: 'POST',
			body: formData
		});

		if (!response.ok) {
			throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
		}

		const data: GeomorphResponse = await response.json();
		processAndUpdateData(data);

		return data.data || [];
	} catch (error) {
		console.error('Error uploading and analyzing file:', error);
		throw error;
	}
}

// Function to reanalyze the current data - now using our server endpoint
export async function reanalyzeData(): Promise<GeomorphData[]> {
	let currentData: GeomorphData[] = [];

	// Get current data from the store
	const unsubscribe = geomorphData.subscribe((value) => {
		currentData = value;
	});
	unsubscribe();

	if (currentData.length === 0) {
		return [];
	}

	try {
		// Call our server endpoint instead of the external API directly
		const response = await fetch('/api/reanalyze', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ data: currentData })
		});

		if (!response.ok) {
			throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
		}

		const data: GeomorphResponse = await response.json();

		// Only update the chart data, not the table data
		if (data.graph_data && data.graph_data.dist) {
			const newChartData = Object.entries(data.graph_data.dist).map(([channelType, value]) => ({
				group: channelType.charAt(0).toUpperCase() + channelType.slice(1),
				value: Number(((value as number) * 100).toFixed(1)) // Convert to percentage with 1 decimal place
			}));
			chartData.set(newChartData);
		}

		return data.data || [];
	} catch (error) {
		console.error('Error reanalyzing data:', error);
		throw error;
	}
}

// Function to reset toggle values
export function resetToggles() {
	geomorphData.update((rows) => {
		return rows.map((row) => ({
			...row,
			interpretable_user: row.interpretable
		}));
	});
}

// Function to update a single toggle
export function updateToggle(rowId: string | number, value: boolean) {
	geomorphData.update((rows) => {
		return rows.map((row) => {
			if (row.id === rowId) {
				return { ...row, interpretable_user: value };
			}
			return row;
		});
	});
}
