const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
	const token = localStorage.getItem("token");
	const headers = {
		"Content-Type": "application/json",
		...(options.headers || {}),
	};

	if (token) {
		headers["Authorization"] = `Bearer ${token}`;
	}

	const res = await fetch(`${API_BASE_URL}${path}`, {
		headers,
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
		console.error(`API Error on ${path}:`, detail);
		throw new Error(detail);
	}

	return res.json();
}

// ─ AUTH ─────────────────────────────────────────────────────
export async function register(email, password, fullName) {
	return request("/auth/register", {
		method: "POST",
		body: JSON.stringify({
			email,
			password,
			full_name: fullName,
		}),
	});
}

export async function login(email, password) {
	const formData = new URLSearchParams();
	formData.append("username", email);
	formData.append("password", password);

	return request("/auth/login", {
		method: "POST",
		body: formData,
		headers: {
			"Content-Type": "application/x-www-form-urlencoded",
		},
	});
}

export async function googleSignIn(token) {
	return request("/auth/google", {
		method: "POST",
		body: JSON.stringify({ token }),
	});
}

export async function getCurrentUser() {
	return request("/auth/me");
}

// ─ PROCUREMENT ──────────────────────────────────────────────
export async function createProcurementRequest(data) {
	return request("/procurement/", {
		method: "POST",
		body: JSON.stringify({
			raw_description: data.title,
			quantity: parseInt(data.quantity) || null,
			budget: parseFloat(data.budget) || null,
			currency: "USD",
			category: data.category || null,
		}),
	});
}

export async function getProcurementRequests(status = null) {
	const queryParams = status ? `?status=${status}` : "";
	return request(`/procurement/${queryParams}`);
}

export async function getProcurementRequest(id) {
	return request(`/procurement/${id}`);
}

export async function cancelProcurement(id) {
	return request(`/procurement/${id}/cancel`, {
		method: "PATCH",
	});
}

export async function deleteProcurement(id) {
	return request(`/procurement/${id}`, {
		method: "DELETE",
	});
}

// ─ QUOTES ──────────────────────────────────────────────────
export async function getQuotes(procurementId) {
	return request(`/quotes/?procurement_id=${procurementId}`);
}

// ─ SUPPLIERS ───────────────────────────────────────────────
export async function getSuppliers(procurementId) {
	return request(`/suppliers/?procurement_id=${procurementId}`);
}

export { API_BASE_URL };
