const statusConfig: Record<string, { label: string; color: string }> = {
  pending: { label: "等待中", color: "bg-gray-100 text-gray-700" },
  crawled: { label: "已爬取", color: "bg-blue-100 text-blue-700" },
  downloading: { label: "下载中", color: "bg-yellow-100 text-yellow-700" },
  parsed: { label: "已解析", color: "bg-indigo-100 text-indigo-700" },
  analyzed: { label: "已分析", color: "bg-purple-100 text-purple-700" },
  embedded: { label: "已嵌入", color: "bg-cyan-100 text-cyan-700" },
  ready: { label: "就绪", color: "bg-green-100 text-green-700" },
};

export default function StatusBadge({ status }: { status: string }) {
  const config = statusConfig[status] ?? {
    label: status,
    color: "bg-gray-100 text-gray-600",
  };
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}
    >
      {config.label}
    </span>
  );
}
