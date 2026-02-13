import { Link } from "react-router";
import { Calendar, Users, Tag } from "lucide-react";
import type { PaperListItem } from "../types/paper";
import StatusBadge from "./StatusBadge";

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function PaperCard({ paper }: { paper: PaperListItem }) {
  return (
    <Link
      to={`/papers/${paper.id}`}
      className="block bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md hover:border-primary-200 transition-all group"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <h3 className="text-base font-semibold text-gray-900 leading-snug group-hover:text-primary-700 transition-colors line-clamp-2">
          {paper.title}
        </h3>
        <StatusBadge status={paper.status} />
      </div>

      {/* Abstract */}
      {paper.abstract && (
        <p className="text-sm text-gray-500 leading-relaxed line-clamp-3 mb-4">
          {paper.abstract}
        </p>
      )}

      {/* Meta row */}
      <div className="flex flex-wrap items-center gap-4 text-xs text-gray-400">
        {paper.authors.length > 0 && (
          <span className="flex items-center gap-1">
            <Users className="w-3.5 h-3.5" />
            {paper.authors
              .slice(0, 3)
              .map((a) => a.name)
              .join(", ")}
            {paper.authors.length > 3 && ` +${paper.authors.length - 3}`}
          </span>
        )}
        {paper.published_at && (
          <span className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5" />
            {formatDate(paper.published_at)}
          </span>
        )}
        {paper.categories && paper.categories.length > 0 && (
          <span className="flex items-center gap-1">
            <Tag className="w-3.5 h-3.5" />
            {paper.categories.slice(0, 3).join(", ")}
          </span>
        )}
        <span className="text-gray-300 font-mono">
          {paper.source}:{paper.source_id}
        </span>
      </div>
    </Link>
  );
}
