import { useEffect, useState } from "react";
import { useParams, Link } from "react-router";
import {
  ArrowLeft,
  Calendar,
  Users,
  Tag,
  ExternalLink,
  FileText,
  Globe,
  Lightbulb,
} from "lucide-react";
import type { PaperDetail } from "../types/paper";
import { fetchPaper } from "../api/client";
import StatusBadge from "../components/StatusBadge";
import LoadingSpinner from "../components/LoadingSpinner";

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export default function PaperDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [paper, setPaper] = useState<PaperDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    loadPaper(Number(id));
  }, [id]);

  async function loadPaper(paperId: number) {
    setLoading(true);
    setError("");
    try {
      const data = await fetchPaper(paperId);
      setPaper(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <LoadingSpinner text="加载论文详情..." />;

  if (error || !paper) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <Link
          to="/papers"
          className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6"
        >
          <ArrowLeft className="w-4 h-4" /> 返回列表
        </Link>
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <p className="text-red-600">{error || "论文不存在"}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      {/* Back link */}
      <Link
        to="/papers"
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6"
      >
        <ArrowLeft className="w-4 h-4" /> 返回列表
      </Link>

      {/* Title & Status */}
      <div className="mb-6">
        <div className="flex items-start gap-3 mb-3">
          <h1 className="text-2xl font-bold text-gray-900 leading-snug flex-1">
            {paper.title}
          </h1>
          <StatusBadge status={paper.status} />
        </div>

        {/* Meta */}
        <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
          {paper.published_at && (
            <span className="flex items-center gap-1.5">
              <Calendar className="w-4 h-4" />
              {formatDate(paper.published_at)}
            </span>
          )}
          <span className="flex items-center gap-1.5 text-gray-400 font-mono text-xs">
            {paper.source}:{paper.source_id}
          </span>
          {paper.pdf_url && (
            <a
              href={paper.pdf_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-primary-600 hover:text-primary-700"
            >
              <ExternalLink className="w-4 h-4" /> PDF
            </a>
          )}
        </div>
      </div>

      {/* Authors */}
      {paper.authors.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-3">
            <Users className="w-4 h-4" /> 作者
          </h2>
          <div className="flex flex-wrap gap-2">
            {paper.authors.map((a) => (
              <span
                key={a.id}
                className="px-3 py-1.5 bg-gray-50 rounded-lg text-sm text-gray-700"
              >
                {a.name}
                {a.affiliation && (
                  <span className="text-gray-400 ml-1">({a.affiliation})</span>
                )}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Categories & Keywords */}
      {(paper.categories?.length || paper.keywords?.length) && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-3">
            <Tag className="w-4 h-4" /> 分类与关键词
          </h2>
          <div className="flex flex-wrap gap-2">
            {paper.categories?.map((c) => (
              <span
                key={c}
                className="px-2.5 py-1 bg-primary-50 text-primary-700 rounded-full text-xs font-medium"
              >
                {c}
              </span>
            ))}
            {paper.keywords?.map((k) => (
              <span
                key={k}
                className="px-2.5 py-1 bg-gray-100 text-gray-600 rounded-full text-xs"
              >
                {k}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Abstract */}
      {paper.abstract && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-3">
            <FileText className="w-4 h-4" /> 摘要
          </h2>
          <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
            {paper.abstract}
          </p>
        </div>
      )}

      {/* Summary (English) */}
      {paper.summary && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-3">
            <Lightbulb className="w-4 h-4" /> AI 总结
          </h2>
          <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
            {paper.summary}
          </p>
        </div>
      )}

      {/* Summary (Chinese) */}
      {paper.summary_zh && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-3">
            <Globe className="w-4 h-4" /> 中文总结
          </h2>
          <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
            {paper.summary_zh}
          </p>
        </div>
      )}

      {/* Contributions */}
      {paper.contributions && paper.contributions.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-3">
            <Lightbulb className="w-4 h-4" /> 主要贡献
          </h2>
          <ul className="space-y-2">
            {paper.contributions.map((c, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                <span className="mt-1 w-5 h-5 rounded-full bg-primary-50 text-primary-600 flex items-center justify-center text-xs font-medium shrink-0">
                  {i + 1}
                </span>
                {c}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Timestamps */}
      <div className="text-xs text-gray-400 mt-6 flex gap-4">
        <span>创建时间: {formatDate(paper.created_at)}</span>
        <span>更新时间: {formatDate(paper.updated_at)}</span>
      </div>
    </div>
  );
}
