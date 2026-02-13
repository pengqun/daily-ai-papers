import { NavLink, Outlet } from "react-router";
import {
  Home,
  FileText,
  Upload,
  MessageCircle,
  BookOpen,
} from "lucide-react";

const navItems = [
  { to: "/", icon: Home, label: "首页" },
  { to: "/papers", icon: FileText, label: "论文" },
  { to: "/submit", icon: Upload, label: "提交" },
  { to: "/chat", icon: MessageCircle, label: "对话" },
];

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col shrink-0">
        {/* Logo */}
        <div className="h-16 flex items-center gap-3 px-6 border-b border-gray-200">
          <BookOpen className="w-7 h-7 text-primary-600" />
          <span className="text-lg font-bold text-gray-900 tracking-tight">
            Daily AI Papers
          </span>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 px-3 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary-50 text-primary-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`
              }
            >
              <Icon className="w-5 h-5" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200">
          <p className="text-xs text-gray-400">
            AI 论文发现与分析平台
          </p>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
