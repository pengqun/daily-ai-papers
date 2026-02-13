import { Loader2 } from "lucide-react";

export default function LoadingSpinner({ text = "加载中..." }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <Loader2 className="w-8 h-8 text-primary-500 animate-spin mb-3" />
      <p className="text-sm text-gray-400">{text}</p>
    </div>
  );
}
