import { json, type RequestHandler } from '@sveltejs/kit';
import { PUBLIC_API_URL } from '$env/static/public';
import type { GeomorphData } from '$lib/types/GeomorphData';

export const POST: RequestHandler = async ({ request }) => {
	const body = await request.json();
	const currentData = body.data as GeomorphData[];

	if (!currentData || !Array.isArray(currentData) || currentData.length === 0) {
		return json({ error: 'No data provided' }, { status: 400 });
	}

	try {
		const response = await fetch(`${PUBLIC_API_URL}/analyze/json`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ data: currentData })
		});

		if (!response.ok) {
			throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
		}

		const data = await response.json();
		return json(data);
	} catch (error) {
		console.error('Error reanalyzing data on server:', error);
		return json(
			{ error: error instanceof Error ? error.message : 'Unknown error' },
			{ status: 500 }
		);
	}
};
