"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Plus, Loader2, TrendingUp } from "lucide-react";
import Link from "next/link";

type Analysis = {
  id: string;
  platform: string;
  title: string;
  sourceUrl: string;
  targetAudience: string;
  createdAt: string;
  generatedAds: { id: string; adType: string; status: string }[];
};

export default function AdAnalyzerPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/ad-analyzer/analyze")
      .then((r) => r.json())
      .then(setAnalyses)
      .finally(() => setLoading(false));
  }, []);

  const totalGenerated = analyses.reduce((sum, a) => sum + a.generatedAds.length, 0);
  const totalUploaded = analyses.reduce(
    (sum, a) => sum + a.generatedAds.filter((g) => g.status === "uploaded").length, 0
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">광고 분석기</h1>
          <p className="text-muted-foreground mt-1">경쟁사/참고 광고 분석 → B+C 영상 자동 생성 → 멀티 플랫폼 업로드</p>
        </div>
        <Link href="/ad-analyzer/create">
          <Button><Plus className="h-4 w-4 mr-2" />새 광고 분석</Button>
        </Link>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        {[
          { label: "분석한 광고", value: analyses.length },
          { label: "생성된 영상", value: totalGenerated },
          { label: "업로드 완료", value: totalUploaded },
        ].map((s) => (
          <Card key={s.label}><CardContent className="pt-6">
            <p className="text-2xl font-bold">{s.value}</p>
            <p className="text-sm text-muted-foreground">{s.label}</p>
          </CardContent></Card>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-16"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /></div>
      ) : analyses.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <TrendingUp className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>아직 분석한 광고가 없습니다</p>
          <Link href="/ad-analyzer/create">
            <Button variant="outline" className="mt-4">첫 광고 분석하기</Button>
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {analyses.map((a) => (
            <Card key={a.id}>
              <CardContent className="flex items-center justify-between py-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="outline" className="text-xs capitalize">{a.platform}</Badge>
                    <p className="font-medium text-sm truncate">{a.title || a.sourceUrl}</p>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    타겟: {a.targetAudience} · {new Date(a.createdAt).toLocaleDateString("ko-KR")}
                  </p>
                  <div className="flex gap-1 mt-1">
                    {a.generatedAds.map((g) => (
                      <Badge key={g.id} variant={g.status === "uploaded" ? "default" : "secondary"} className="text-xs">
                        {g.adType === "B_slideshow" ? "B(슬라이드)" : "C(나레이션)"} · {g.status === "uploaded" ? "업로드됨" : "생성됨"}
                      </Badge>
                    ))}
                  </div>
                </div>
                <Link href="/ad-analyzer/create">
                  <Button variant="outline" size="sm">다시 생성</Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
