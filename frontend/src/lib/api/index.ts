const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function checkBackendHealth() {
  const response = await fetch(`${API_BASE_URL}/health`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
  
  if (!response.ok) {
    throw new Error("Failed to fetch backend health");
  }
  
  return response.json();
}
