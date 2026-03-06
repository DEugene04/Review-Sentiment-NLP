import { motion } from "framer-motion";

interface StatCardProps {
  value: string;
  label: string;
  delay?: number;
}

const StatCard = ({ value, label, delay = 0 }: StatCardProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: "easeOut" }}
      className="group relative overflow-hidden rounded-2xl bg-sage-light/60 border border-sage/30 px-8 py-7 shadow-soft backdrop-blur-sm transition-all hover:shadow-card hover:border-sage/50"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-sage-light/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      <div className="relative">
        <p className="font-heading text-4xl font-bold tracking-tight text-foreground">
          {value}
        </p>
        <p className="mt-1.5 text-sm font-medium text-muted-foreground">
          {label}
        </p>
      </div>
    </motion.div>
  );
};

export default StatCard;
