import { useState } from "react";
import { Upload, CheckCircle, XCircle, AlertCircle, Info } from "lucide-react";
import type { SubmitPaperResult } from "../types/paper";
import { submitPapers } from "../api/client";

export default function SubmitPage() {
  const [source, setSource] = useState<"arxiv" | "semantic_scholar">("arxiv");
  const [idsText, setIdsText] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SubmitPaperResult[] | null>(null);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setResults(null);

    const ids = idsText
      .split(/[\n,]+/)
      .map((s) => s.trim())
      .filter(Boolean);

    if (ids.length === 0) {
      setError("请输入至少一个论文 ID");
      return;
    }
    if (ids.length > 50) {
      setError("每次最多提交 50 篇论文");
      return;
    }

    setLoading(true);
    try {
      const res = await submitPapers({ source, paper_ids: ids });
      setResults(res.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "提交失败");
    } finally {
      setLoading(false);
    }
  }

  const statusIcon = (status: string) => {
    switch (status) {
      case "queued":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "duplicate":
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default:
        return <XCircle className="w-4 h-4 text-red-500" />;
    }
  };

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">提交论文</h1>
        <p className="text-gray-500">
          手动提交论文 ID，系统将自动爬取并处理
        </p>
      </div>

      {/* Info box */}
      <div className="bg-primary-50 border border-primary-200 rounded-xl p-4 mb-6 flex gap-3">
        <Info className="w-5 h-5 text-primary-600 shrink-0 mt-0.5" />
        <div className="text-sm text-primary-700">
          <p className="font-medium mb-1">支持的 ID 格式</p>
          <p>arXiv: <code className="bg-primary-100 px-1 rounded">1706.03762</code> 或 <code className="bg-primary-100 px-1 rounded">2401.00001</code></p>
          <p>每行一个 ID，或用逗号分隔</p>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-gray-200 p-6">
        {/* Source selector */}
        <div className="mb-5">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            来源
          </label>
          <div className="flex gap-3">
            {[
              { value: "arxiv" as const, label: "arXiv" },
              { value: "semantic_scholar" as const, label: "Semantic Scholar" },
            ].map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setSource(opt.value)}
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
                  source === opt.value
                    ? "bg-primary-50 border-primary-300 text-primary-700"
                    : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Paper IDs input */}
        <div className="mb-5">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            论文 ID
          </label>
          <textarea
            value={idsText}
            onChange={(e) => setIdsText(e.target.value)}
            placeholder={"1706.03762\n2401.00001\n2310.12345"}
            rows={6}
            className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-y"
          />
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {error}
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors disabled:opacity-50"
        >
          <Upload className="w-4 h-4" />
          {loading ? "提交中..." : "提交论文"}
        </button>
      </form>

      {/* Results */}
      {results && (
        <div className="mt-6 bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-5 py-3 border-b border-gray-200 bg-gray-50">
            <h3 className="text-sm font-semibold text-gray-700">
              提交结果 ({results.length} 篇)
            </h3>
          </div>
          <div className="divide-y divide-gray-100">
            {results.map((r) => (
              <div
                key={r.source_id}
                className="px-5 py-3 flex items-center gap-3"
              >
                {statusIcon(r.status)}
                <span className="font-mono text-sm text-gray-700">
                  {r.source_id}
                </span>
                <span className="text-sm text-gray-400 flex-1">
                  {r.message}
                </span>
                <span className="text-xs text-gray-400 capitalize">
                  {r.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
