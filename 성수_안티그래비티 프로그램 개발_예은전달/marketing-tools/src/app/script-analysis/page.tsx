import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { FileText, BarChart3 } from "lucide-react";

const features = [
  {
    title: "블로그 → 광고 대본 변환",
    description: "블로그 글을 붙여넣으면 AI가 숏폼 광고 대본으로 변환합니다",
    href: "/script-analysis/blog-to-script",
    icon: FileText,
  },
  {
    title: "대본 패턴 분석",
    description: "기존 대본들을 분석하여 성공 패턴을 추출합니다",
    href: "/script-analysis/pattern-analysis",
    icon: BarChart3,
  },
];

export default function ScriptAnalysisPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">대본분석</h1>
      <p className="text-muted-foreground mb-6">
        블로그를 광고 대본으로 변환하고 성공 패턴을 분석합니다
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {features.map((feature) => (
          <Link key={feature.href} href={feature.href}>
            <Card className="hover:border-primary transition-colors cursor-pointer h-full">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <feature.icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{feature.title}</CardTitle>
                    <CardDescription>{feature.description}</CardDescription>
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
