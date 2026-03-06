const API_BASE = "http://127.0.0.1:8000";

export async function get_reviews(business_id: string) {
  const res = await fetch(`${API_BASE}/businesses/${business_id}/get_reviews`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function previewImport(business_id: string, file: File) {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(
    `${API_BASE}/businesses/${business_id}/reviews/import/preview`,
    {
      method: "POST",
      body: form,
    },
  );
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function commitImport(business_id: string, reviews: any[]) {
  const res = await fetch(
    `${API_BASE}/businesses/${business_id}/reviews/import/commit`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reviews }),
    },
  );
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function runAnalysis(
  businessId: string,
  parameters: Record<string, any>,
) {
  const res = await fetch(
    `${API_BASE}/businesses/${businessId}/analysis-runs`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        parameters_json: parameters,
      }),
    },
  );
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getDashboard(businessId: string) {
  const res = await fetch(`${API_BASE}/businesses/${businessId}/dashboard`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
