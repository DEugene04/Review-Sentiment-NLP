import { motion } from "framer-motion";
import { Plus } from "lucide-react";
import StatCard from "../components/StatCard";
import ReviewsTable from "../components/ReviewsTable";
import { useEffect, useState } from "react";

type DashboardResponse = {
  total_reviews: number;
  negative_reviews_pct: number;
  negative_ratio: number;
  top_negative_topic: object;
  top_positive_topic: object;
};

const API_BASE = "http://127.0.0.1:8000";
const BUSINESS_ID = "65bdf616-863b-4b42-9817-f7f18662d45e"; // Change later or pull from route params

const Index = () => {
  // Defining variables
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ac = new AbortController();

    async function load() {
      try {
        const res = await fetch(
          `${API_BASE}/businesses/${BUSINESS_ID}/dashboard`,
          { signal: ac.signal },
        );

        console.log("response status: ", res.status);

        // Handles server errors such as 404, 500, 401, etc
        if (!res.ok) {
          const text = await res.text();
          throw new Error(`API ${res.status}: ${text}`);
        }

        const json = (await res.json()) as DashboardResponse;
        console.log("Parses JSON: ", json);
        setData(json);
      } catch (e: any) {
        // Handles runtime/ network errors such as network disconnected, parse error, etc
        if (e?.name === "AbortError") return;
        console.error("FETCH FAILED:", e);
        setError(e.message ?? "failed to load");
      } finally {
        setLoading(false);
      }
    }

    load();
    return () => ac.abort();
  }, []);

  // Setting variables to store API response
  const totalReviews = data?.total_reviews;
  const negative_ratio = data?.negative_ratio;
  const top_positive_topic = data?.top_positive_topic;
  const top_negative_topic = data?.top_negative_topic;

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
          <button className="inline-flex items-center gap-2 rounded-full bg-lavender px-5 py-2.5 text-sm font-medium text-accent-foreground shadow-soft transition-all hover:shadow-card hover:brightness-105 active:scale-[0.97]">
            <Plus className="h-4 w-4" />
            Add Review
          </button>
        </motion.div>

        {/* Stat Cards */}
        <div className="mt-10 grid grid-cols-1 gap-5 sm:grid-cols-3">
          <StatCard
            value={String(totalReviews)}
            label="Total Reviews"
            delay={0.1}
          />
          <StatCard
            value={`${negative_ratio}%`}
            label="Negative Reviews"
            delay={0.15}
          />
          <StatCard
            value={String(top_negative_topic?.label)}
            label="Top negative topic"
            delay={0.2}
          />
          <StatCard
            value={String(top_positive_topic?.label)}
            label="Top positive topic"
            delay={0.25}
          />
        </div>

        {/* Reviews Table */}
        <ReviewsTable />
      </div>
    </div>
  );
};

export default Index;
