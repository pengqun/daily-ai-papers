import { Inbox } from "lucide-react";

export default function EmptyState({
  title = "暂无数据",
  description = "当前没有可显示的内容",
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <Inbox className="w-12 h-12 text-gray-300 mb-4" />
      <h3 className="text-lg font-medium text-gray-500 mb-1">{title}</h3>
      <p className="text-sm text-gray-400">{description}</p>
    </div>
  );
}
