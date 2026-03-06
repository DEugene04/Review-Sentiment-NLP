import { useEffect, useState, useRef } from "react";
import { previewImport, commitImport, runAnalysis, getDashboard } from "../api";
import { motion } from "framer-motion";
import { Plus } from "lucide-react";
import StatCard from "../components/StatCard";
import ReviewsTable from "../components/ReviewsTable";

const business_id = "65bdf616-863b-4b42-9817-f7f18662d45e";

type PreviewValidRow = Record<string, unknown>;

type ImportPreviewResponse = {
  valid_count: number;
  error_count: number;
  needs_mapping: boolean;
  columns: string[];
  preview_valid_rows: PreviewValidRow[];
};

type Topic = {
  topic_id: string;
  label: string;
  size: number;
  negative_ratio: number;
  impact_score: number;
};

type TopicSummary = {
  label: string;
};

type DashboardResponse = {
  total_reviews: number;
  negative_reviews_pct: number;
  negative_ratio: number;
  top_negative_topic: object;
  top_positive_topic: object;
};

type LoadingState = "" | "preview" | "commit" | "run";

const Index_copy = () => {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any | null>(null);
  const [error, setError] = useState<string>("");
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState<LoadingState>("");
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  // Call api to get newest data on dashboard
  async function refreshDashboard() {
    setError("");
    try {
      const d = await getDashboard(business_id);
      setDashboard(d);
    } catch (error: any) {
      console.error("FETCH FAILED:", error);
      setError(error.message ?? "failed to load");
    }
  }

  useEffect(() => {
    refreshDashboard().catch(() => {});
  }, []);

  async function handlePreview() {
    setLoading("preview");
    if (!file) return;
    setError("");
    try {
      const p = (await previewImport(
        business_id,
        file,
      )) as ImportPreviewResponse;
      setPreview(p);
      setIsPreviewOpen(true);
    } catch (error: any) {
      setError(error.message || "Preview failed");
    } finally {
      setLoading("");
    }
  }

  function getDetectedMapping(preview: any) {
    if (!preview) return null;

    if (preview.detected_mapping) return preview.detected_mapping;
    if (preview.mapping) return preview.mapping;
    // Fallback
    const r0 = preview.preview_valid_rows?.[0];
    return r0?.extra?.raw?.detected_mapping ?? null;
  }

  async function handleCommit(): Promise<void> {
    setLoading("commit");
    setError("");
    try {
      const validRows = preview?.preview_valid_rows ?? [];
      console.log("ini valid rowsnya", validRows);
      if (!validRows.length) throw new Error("No valid rows to import.");
      await commitImport(business_id, validRows);
      setPreview(null);
      await refreshDashboard();
    } catch (error: any) {
      setError(error.message || "Commit failed");
    } finally {
      setLoading("");
    }
  }

  async function handleRun(): Promise<void> {
    setLoading("run");
    setError("");
    try {
      await runAnalysis(business_id, {
        embedding_model: "multilingual-e5-small",
        clusterer: "kmeans",
        k: 5,
      });
      await refreshDashboard();
    } catch (error: any) {
      setError(error.message || "Run analysis failed");
    } finally {
      setLoading("");
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-5xl px-6 py-12 sm:px-8 lg:py-16">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex items-center justify-between"
        >
          <div>
            <h1 className="font-heading text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
              Customer Insights
            </h1>
            <p className="mt-1.5 text-sm text-muted-foreground">
              Monitor reviews and sentiment across topics
            </p>
            {loading && (
              <p className="mt-2 text-sm text-muted-foreground">Loading...</p>
            )}
            {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
          </div>
          <input
            type="file"
            ref={fileInputRef}
            accept=".csv"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-2 rounded-full bg-lavender px-5 py-2.5 text-sm font-medium text-accent-foreground shadow-soft transition-all hover:shadow-card hover:brightness-105 active:scale-[0.97]"
            >
              <Plus className="h-4 w-4" />
              Add Review
            </button>

            <div className="min-w-0">
              {file ? (
                <p className="truncate text-sm text-muted-foreground">
                  {file.name}
                </p>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Choose a .csv file to preview and import
                </p>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <button
              type="button"
              onClick={handlePreview}
              disabled={!file || loading !== ""}
              className="inline-flex items-center justify-center rounded-full border border-border bg-background px-5 py-2.5 text-sm font-medium text-foreground shadow-soft transition-all hover:shadow-card disabled:opacity-50"
            >
              {loading === "preview" ? "Previewing..." : "Preview Import"}
            </button>

            <button
              type="button"
              onClick={handleRun}
              disabled={loading !== ""}
              className="inline-flex items-center justify-center rounded-full border border-border bg-background px-5 py-2.5 text-sm font-medium text-foreground shadow-soft transition-all hover:shadow-card disabled:opacity-50"
            >
              {loading === "run" ? "Running..." : "Run Analysis"}
            </button>
          </div>
        </motion.div>

        {/* Stat Cards */}
        <div className="mt-10 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            value={String(dashboard?.total_reviews)}
            label="Total Reviews"
            delay={0.1}
          />
          <StatCard
            value={`${dashboard?.negative_ratio}%`}
            label="Negative Reviews"
            delay={0.15}
          />
          <StatCard
            value={String(dashboard?.top_negative_topic?.label)}
            label="Top negative topic"
            delay={0.2}
          />
          <StatCard
            value={String(dashboard?.top_positive_topic?.label)}
            label="Top positive topic"
            delay={0.25}
          />
        </div>

        {/* Reviews Table */}
        <ReviewsTable />

        {/* Preview modal */}
        {isPreviewOpen && preview && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
            onClick={() => setIsPreviewOpen(false)} // click outside closes
          >
            <div
              className="w-full max-w-5xl max-h-[80vh] overflow-auto rounded-2xl bg-white p-4 shadow-xl"
              onClick={(e: React.MouseEvent<HTMLDivElement>) =>
                e.stopPropagation()
              } // prevent closing when clicking inside
              role="dialog"
              aria-modal="true"
              aria-label="Confirm Import Preview"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="m-0 text-lg font-semibold text-gray-900">
                    Confirm Import Preview
                  </h2>
                  <div className="mt-1 text-sm text-gray-600">
                    Valid:{" "}
                    <span className="font-semibold text-gray-900">
                      {preview.valid_count}
                    </span>{" "}
                    · Errors:{" "}
                    <span className="font-semibold text-gray-900">
                      {preview.error_count}
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => setIsPreviewOpen(false)}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50"
                  aria-label="Close"
                >
                  ✕
                </button>
              </div>

              {/* Mapping table */}
              <h3 className="mt-4 text-sm font-semibold text-gray-900">
                Detected Mapping
              </h3>

              {((): React.ReactNode => {
                const mapping = getDetectedMapping(preview) as
                  | Record<string, unknown>
                  | null
                  | undefined;
                if (!mapping)
                  return (
                    <div className="mt-2 text-sm text-gray-500">
                      No mapping found.
                    </div>
                  );

                const entries = Object.entries(mapping);

                return (
                  <div className="mt-2 overflow-x-auto rounded-2xl border border-gray-200">
                    <table className="w-full border-collapse text-sm">
                      <thead>
                        <tr className="border-b border-gray-200 text-left text-gray-700">
                          <th className="px-3 py-3 font-semibold">
                            CSV column detected
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {entries.map(([canonical, csvCol]) => (
                          <tr
                            key={canonical}
                            className="border-b border-gray-100 last:border-b-0"
                          >
                            <td className="px-3 py-3 font-mono text-gray-900">
                              {String(csvCol)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                );
              })()}

              {/* Row preview table */}
              <h3 className="mt-4 text-sm font-semibold text-gray-900">
                Parsed Rows Preview
              </h3>

              <div className="mt-2 overflow-x-auto rounded-2xl border border-gray-200">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 text-left text-gray-700">
                      <th className="px-3 py-3 font-semibold">rating</th>
                      <th className="px-3 py-3 font-semibold">text</th>
                      <th className="px-3 py-3 font-semibold">review_date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(preview.preview_valid_rows ?? []).slice(0, 10).map(
                      (
                        r: {
                          rating?: number | null;
                          text?: string | null;
                          review_date?: string | null;
                        },
                        idx: number,
                      ) => (
                        <tr
                          key={idx}
                          className="border-b border-gray-100 last:border-b-0"
                        >
                          <td className="px-3 py-3 text-gray-900">
                            {r.rating ?? "-"}
                          </td>
                          <td className="px-3 py-3 text-gray-900">
                            <div className="max-w-[520px] truncate">
                              {r.text ?? "-"}
                            </div>
                          </td>
                          <td className="px-3 py-3 text-gray-900">
                            {r.review_date ?? "-"}
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>

              {/* Actions */}
              <div className="mt-4 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsPreviewOpen(false)}
                  className="inline-flex items-center justify-center rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-900 hover:bg-gray-50"
                >
                  Cancel
                </button>

                <button
                  type="button"
                  onClick={async () => {
                    await handleCommit(); // your existing commit logic
                    setIsPreviewOpen(false); // close modal after success
                  }}
                  disabled={loading !== ""}
                  className="inline-flex items-center justify-center rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {loading === "commit" ? "Importing..." : "Confirm Import"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Index_copy;
