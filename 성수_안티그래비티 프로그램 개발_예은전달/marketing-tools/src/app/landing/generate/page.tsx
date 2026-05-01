"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Loader2, Download, Eye, Code, EyeOff } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

function GenerateContent() {
  const searchParams = useSearchParams();
  const initialAnalysis = searchParams.get("analysis") ?? "";
  const projectId = searchParams.get("id") ?? "";

  const [analysis, setAnalysis] = useState(initialAnalysis);
  const [customInstructions, setCustomInstructions] = useState("");
  const [html, setHtml] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPreview, setShowPreview] = useState(true);

  const handleGenerate = async () => {
    if (!analysis.trim()) return;
    setLoading(true);
    setError("");
    setHtml("");

    try {
      const res = await fetch("/api/landing/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          analysisResult: analysis,
          projectId: projectId || undefined,
          customInstructions: customInstructions || undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setHtml(data.html);
    } catch (err) {
      setError(err instanceof Error ? err.message : "오류가 발생했습니다");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "landing-page.html";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-6xl">
      <Link
        href="/landing"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4"
      >
        <ArrowLeft className="h-4 w-4" />
        랜딩페이지
      </Link>

      <h1 className="text-3xl font-bold mb-2">랜딩페이지 생성</h1>
      <p className="text-muted-foreground mb-6">
        분석 결과를 기반으로 HTML 랜딩페이지를 자동 생성합니다
      </p>

      {!html ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>분석 결과</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="랜딩페이지 분석 결과를 붙여넣거나 직접 요구사항을 작성하세요..."
                value={analysis}
                onChange={(e) => setAnalysis(e.target.value)}
                rows={12}
                className="resize-none"
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>추가 요구사항 (선택)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="예: 파란색 톤으로 해주세요, CTA 버튼을 3개 추가해주세요..."
                value={customInstructions}
                onChange={(e) => setCustomInstructions(e.target.value)}
                rows={8}
                className="resize-none"
              />
              <Button
                onClick={handleGenerate}
                disabled={loading || !analysis.trim()}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    페이지 생성 중...
                  </>
                ) : (
                  "HTML 페이지 생성"
                )}
              </Button>
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => setShowPreview(!showPreview)}>
              {showPreview ? (
                <>
                  <Code className="h-4 w-4 mr-2" />
                  코드 보기
                </>
              ) : (
                <>
                  <Eye className="h-4 w-4 mr-2" />
                  미리보기
                </>
              )}
            </Button>
            <Button onClick={handleDownload}>
              <Download className="h-4 w-4 mr-2" />
              HTML 다운로드
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                setHtml("");
              }}
            >
              다시 생성
            </Button>
          </div>

          {showPreview ? (
            <Card className="overflow-hidden">
              <iframe
                srcDoc={html}
                className="w-full border-0"
                style={{ height: "80vh" }}
                title="Landing Page Preview"
                sandbox="allow-scripts"
              />
            </Card>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <pre className="text-xs overflow-auto max-h-[80vh] p-4 bg-muted rounded-lg">
                  <code>{html}</code>
                </pre>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm mt-4">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center justify-center py-16">
          <Loader2 className="h-10 w-10 animate-spin text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            랜딩페이지를 생성하고 있습니다...
          </p>
        </div>
      )}
    </div>
  );
}

export default function LandingGeneratePage() {
  return (
    <Suspense>
      <GenerateContent />
    </Suspense>
  );
}
