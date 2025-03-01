import { json, type RequestHandler } from '@sveltejs/kit';
import { PUBLIC_API_URL } from '$env/static/public';

export const POST: RequestHandler = async ({ request }) => {
	const formData = await request.formData();
	const file = formData.get('file') as File;

	if (!file) {
		return json({ error: 'No file uploaded' }, { status: 400 });
	}

	try {
		const serverFormData = new FormData();
		serverFormData.append('file', file);

		const response = await fetch(`${PUBLIC_API_URL}/analyze/file`, {
			method: 'POST',
			body: serverFormData
		});

		if (!response.ok) {
			throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
		}

		const data = await response.json();
		return json(data);
	} catch (error) {
		console.error('Error processing file on server:', error);
		return json(
			{ error: error instanceof Error ? error.message : 'Unknown error' },
			{ status: 500 }
		);
	}
};
