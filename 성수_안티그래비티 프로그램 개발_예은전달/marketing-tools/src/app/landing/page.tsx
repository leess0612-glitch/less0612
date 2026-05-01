import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import Link from "next/link";
import { Search, Wand2 } from "lucide-react";

const features = [
  {
    title: "랜딩페이지 분석",
    description: "URL을 입력하면 페이지 구조, CTA, 카피를 AI가 분석합니다",
    href: "/landing/analyze",
    icon: Search,
  },
  {
    title: "랜딩페이지 생성",
    description: "분석 결과를 기반으로 유사한 HTML 페이지를 자동 생성합니다",
    href: "/landing/generate",
    icon: Wand2,
  },
];

export default function LandingPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">랜딩페이지 분석 & 생성</h1>
      <p className="text-muted-foreground mb-6">
        URL을 분석하고 유사한 랜딩페이지를 자동 생성합니다
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
