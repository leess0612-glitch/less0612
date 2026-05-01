import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Film, FileText, Globe, Calculator } from "lucide-react";

const tools = [
  {
    title: "릴스 광고 자동화",
    description: "대본 생성부터 업로드, 성과 추적까지 자동화",
    href: "/reels",
    icon: Film,
  },
  {
    title: "대본분석",
    description: "블로그를 광고 대본으로 변환하고 성공 패턴을 분석",
    href: "/script-analysis",
    icon: FileText,
  },
  {
    title: "랜딩페이지 분석 & 생성",
    description: "URL을 분석하고 유사한 랜딩페이지를 자동 생성",
    href: "/landing",
    icon: Globe,
  },
  {
    title: "정산계산기",
    description: "수수료율과 비용을 고려한 수익 정산",
    href: "/calculator",
    icon: Calculator,
  },
];

export default function Home() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">까치 마케팅 도구</h1>
      <p className="text-muted-foreground mb-8">
        마케팅 업무를 위한 자동화 도구 모음
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {tools.map((tool) => (
          <Link key={tool.href} href={tool.href}>
            <Card className="hover:border-primary transition-colors cursor-pointer h-full">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <tool.icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{tool.title}</CardTitle>
                    <CardDescription>{tool.description}</CardDescription>
                  </div>
                </div>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
