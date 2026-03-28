const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
	const res = await fetch(`${API_BASE_URL}${path}`, {
		headers: {
			"Content-Type": "application/json",
			...(options.headers || {}),
		},
		...options,
	});

	if (!res.ok) {
		let detail = `HTTP ${res.status}`;
		try {
			const data = await res.json();
			detail = data?.detail || detail;
		} catch {
			// Ignore JSON parse errors for non-JSON responses.
		}
		throw new Error(detail);
	}

	return res.json();
}

export async function googleSignIn(token) {
	return request("/auth/google", {
		method: "POST",
		body: JSON.stringify({ token }),
	});
}

export { API_BASE_URL };
