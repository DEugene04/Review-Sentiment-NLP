import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { get_reviews } from "../api";

// interface ReviewRow {
//   topic: string;
//   review: string;
//   negativePercent: string;
//   impactScore: number;
// }

// const reviews: ReviewRow[] = [
//   {
//     topic: "Packaging, Delivery",
//     review: "Deliverynya lama bgt cok, dan pas sampe tumpah2",
//     negativePercent: "2/20",
//     impactScore: 7.0,
//   },
//   {
//     topic: "Packaging, Delivery",
//     review: "Kuahnya banyak yang tumpah",
//     negativePercent: "4/25",
//     impactScore: 6.7,
//   },
//   {
//     topic: "Packaging, Delivery",
//     review: "Kuahnya sudah ga panas pas sampe",
//     negativePercent: "3/21",
//     impactScore: 6.5,
//   },
//   {
//     topic: "Taste",
//     review: "Rasanya terlalu asin",
//     negativePercent: "1/40",
//     impactScore: 6.2,
//   },
// ];

const ReviewsTable = () => {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [reviews, setReviews] = useState<any[]>([]);
  const business_id = "65bdf616-863b-4b42-9817-f7f18662d45e";

  useEffect(() => {
    async function fetchReviews() {
      try {
        const data = await get_reviews(business_id);
        setReviews(data.reviews);
        console.log(data);
      } catch (error: any) {
        setError(error.message || "Failed to load the reviews");
      } finally {
        setLoading(false);
      }
    }

    fetchReviews();
  }, []);

  const columns = ["Topic", "Reviews", "Label"] as const;

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="bg-red-500">{error}</div>;
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.3, ease: "easeOut" }}
      className="mt-10"
    >
      <div className="overflow-x-auto rounded-xl border border-border bg-card shadow-soft">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-6 py-4 text-left font-heading text-xs font-semibold uppercase tracking-wider text-lavender-foreground"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {reviews.map((row, i) => (
              <motion.tr
                key={i}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: 0.4 + i * 0.08 }}
                className="border-b border-border/50 last:border-0 transition-colors hover:bg-muted/40"
              >
                <td className="px-6 py-4 font-medium text-foreground">
                  <span className="inline-flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-sage-dark" />
                    {row.topic}
                  </span>
                </td>
                <td className="px-6 py-4 text-muted-foreground max-w-xs">
                  {row.reviews}
                </td>
                <td className="px-6 py-4">
                  <span
                    className={
                      row.label == "negative"
                        ? `inline-flex items-center rounded-full bg-destructive/10 text-destructive px-2.5 py-0.5 text-xs font-semibold`
                        : `inline-flex items-center rounded-full bg-green-400/10 text-green-950 px-2.5 py-0.5 text-xs font-semibold`
                    }
                  >
                    {row.label}
                  </span>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
};

export default ReviewsTable;
