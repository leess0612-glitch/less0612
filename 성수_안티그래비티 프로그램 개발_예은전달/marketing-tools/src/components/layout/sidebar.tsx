"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Film,
  FileText,
  Globe,
  Calculator,
  LayoutDashboard,
  Camera,
  TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  {
    title: "대시보드",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    title: "광고 분석기",
    href: "/ad-analyzer",
    icon: TrendingUp,
  },
  {
    title: "인스타 광고 자동화",
    href: "/instagram",
    icon: Camera,
  },
  {
    title: "릴스 광고 자동화",
    href: "/reels",
    icon: Film,
  },
  {
    title: "대본분석",
    href: "/script-analysis",
    icon: FileText,
  },
  {
    title: "랜딩페이지",
    href: "/landing",
    icon: Globe,
  },
  {
    title: "정산계산기",
    href: "/calculator",
    icon: Calculator,
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r bg-card min-h-screen p-4 flex flex-col">
      <div className="mb-8">
        <h1 className="text-xl font-bold">까치 마케팅 도구</h1>
        <p className="text-sm text-muted-foreground mt-1">Marketing Tools</p>
      </div>
      <nav className="flex flex-col gap-1">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.title}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
