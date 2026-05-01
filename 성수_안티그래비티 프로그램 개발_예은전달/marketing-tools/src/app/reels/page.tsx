import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import Link from "next/link";
import { Sparkles, Film, Upload, BarChart3 } from "lucide-react";

const steps = [
  {
    title: "1. 대본 생성",
    description: "AI로 플랫폼별 광고 대본을 자동 생성",
    href: "/reels/script",
    icon: Sparkles,
  },
  {
    title: "2. 영상 제작",
    description: "대본을 영상으로 만들기 위한 가이드와 도구",
    href: "/reels/video",
    icon: Film,
  },
  {
    title: "3. 업로드 관리",
    description: "릴스, 틱톡, 쇼츠 업로드 정보 등록",
    href: "/reels/upload",
    icon: Upload,
  },
  {
    title: "4. 성과 추적",
    description: "조회수, 좋아요, CTR 등 성과 지표 대시보드",
    href: "/reels/tracking",
    icon: BarChart3,
  },
];

export default function ReelsPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">릴스 광고 자동화</h1>
      <p className="text-muted-foreground mb-6">
        대본 생성부터 업로드, 성과 추적까지 전체 파이프라인
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {steps.map((step) => (
          <Link key={step.href} href={step.href}>
            <Card className="hover:border-primary transition-colors cursor-pointer h-full">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <step.icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{step.title}</CardTitle>
                    <CardDescription>{step.description}</CardDescription>
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
