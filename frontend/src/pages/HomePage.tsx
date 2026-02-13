import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  FileText,
  TrendingUp,
  Clock,
  ArrowRight,
  RefreshCw,
  Zap,
} from "lucide-react";
import type { PaperListItem } from "../types/paper";
import { fetchPapers, triggerCrawl } from "../api/client";
import PaperCard from "../components/PaperCard";
import LoadingSpinner from "../components/LoadingSpinner";

export default function HomePage() {
  const [papers, setPapers] = useState<PaperListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [crawling, setCrawling] = useState(false);

  useEffect(() => {
    loadPapers();
  }, []);

  async function loadPapers() {
    setLoading(true);
    try {
      const data = await fetchPapers({ page: 1, page_size: 6 });
      setPapers(data);
    } catch {
      // API not available — show empty state
    } finally {
      setLoading(false);
    }
  }

  async function handleCrawl() {
    setCrawling(true);
    try {
      await triggerCrawl();
    } catch {
      // ignore
    } finally {
      setCrawling(false);
    }
  }

  const stats = [
    {
      label: "论文总数",
      value: papers.length > 0 ? `${papers.length}+` : "—",
      icon: FileText,
      color: "text-primary-600 bg-primary-50",
    },
    {
      label: "已分析",
      value: papers.filter((p) => ["analyzed", "embedded", "ready"].includes(p.status)).length || "—",
      icon: TrendingUp,
      color: "text-green-600 bg-green-50",
    },
    {
      label: "处理中",
      value: papers.filter((p) => ["pending", "crawled", "downloading", "parsed"].includes(p.status)).length || "—",
      icon: Clock,
      color: "text-yellow-600 bg-yellow-50",
    },
  ];

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Hero */}
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Daily AI Papers
        </h1>
        <p className="text-gray-500 text-lg">
          发现、分析、翻译最新 AI 研究论文
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
        {stats.map(({ label, value, icon: Icon, color }) => (
          <div
            key={label}
            className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-4"
          >
            <div className={`w-11 h-11 rounded-lg flex items-center justify-center ${color}`}>
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{value}</p>
              <p className="text-sm text-gray-400">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="flex gap-3 mb-10">
        <button
          onClick={handleCrawl}
          disabled={crawling}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${crawling ? "animate-spin" : ""}`} />
          {crawling ? "爬取中..." : "触发爬取"}
        </button>
        <Link
          to="/submit"
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-white text-gray-700 border border-gray-200 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
        >
          <Zap className="w-4 h-4" />
          手动提交论文
        </Link>
      </div>

      {/* Recent Papers */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">最新论文</h2>
        <Link
          to="/papers"
          className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
        >
          查看全部 <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : papers.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-500 mb-2">
            暂无论文
          </h3>
          <p className="text-sm text-gray-400 mb-6">
            点击"触发爬取"从 arXiv 获取最新论文，或手动提交论文 ID
          </p>
          <button
            onClick={handleCrawl}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
          >
            <RefreshCw className="w-4 h-4" />
            开始爬取
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {papers.map((paper) => (
            <PaperCard key={paper.id} paper={paper} />
          ))}
        </div>
      )}
    </div>
  );
}
