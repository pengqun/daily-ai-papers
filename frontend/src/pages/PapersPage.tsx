import { useEffect, useState } from "react";
import { Search, Filter } from "lucide-react";
import type { PaperListItem } from "../types/paper";
import { fetchPapers } from "../api/client";
import PaperCard from "../components/PaperCard";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";

const CATEGORIES = [
  { value: "", label: "全部分类" },
  { value: "cs.AI", label: "cs.AI" },
  { value: "cs.CL", label: "cs.CL" },
  { value: "cs.CV", label: "cs.CV" },
  { value: "cs.LG", label: "cs.LG" },
  { value: "stat.ML", label: "stat.ML" },
];

const STATUSES = [
  { value: "", label: "全部状态" },
  { value: "pending", label: "等待中" },
  { value: "crawled", label: "已爬取" },
  { value: "parsed", label: "已解析" },
  { value: "analyzed", label: "已分析" },
  { value: "ready", label: "就绪" },
];

export default function PapersPage() {
  const [papers, setPapers] = useState<PaperListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    loadPapers();
  }, [page, category, status]);

  async function loadPapers() {
    setLoading(true);
    try {
      const data = await fetchPapers({
        page,
        page_size: 20,
        category: category || undefined,
        status: status || undefined,
      });
      setPapers(data);
    } catch {
      setPapers([]);
    } finally {
      setLoading(false);
    }
  }

  const filtered = searchQuery
    ? papers.filter(
        (p) =>
          p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          p.abstract?.toLowerCase().includes(searchQuery.toLowerCase()),
      )
    : papers;

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">论文列表</h1>
        <p className="text-gray-500">浏览和搜索 AI 领域最新论文</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
        <div className="flex flex-wrap gap-3">
          {/* Search */}
          <div className="flex-1 min-w-[240px] relative">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="搜索论文标题或摘要..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Category filter */}
          <div className="relative">
            <Filter className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <select
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setPage(1);
              }}
              className="pl-10 pr-8 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none cursor-pointer"
            >
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          {/* Status filter */}
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="px-4 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none cursor-pointer"
          >
            {STATUSES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <LoadingSpinner />
      ) : filtered.length === 0 ? (
        <EmptyState
          title="没有找到论文"
          description="尝试调整筛选条件或触发一次新的爬取"
        />
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
            {filtered.map((paper) => (
              <PaperCard key={paper.id} paper={paper} />
            ))}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 text-sm border border-gray-200 rounded-lg bg-white hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              上一页
            </button>
            <span className="px-4 py-2 text-sm text-gray-500">
              第 {page} 页
            </span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={papers.length < 20}
              className="px-4 py-2 text-sm border border-gray-200 rounded-lg bg-white hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              下一页
            </button>
          </div>
        </>
      )}
    </div>
  );
}
