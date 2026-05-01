"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Loader2, Copy, Check } from "lucide-react";
import Link from "next/link";

export default function PatternAnalysisPage() {
  const [scripts, setScripts] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const handleSubmit = async () => {
    if (!scripts.trim()) return;
    setLoading(true);
    setError("");
    setResult("");

    try {
      const res = await fetch("/api/script-analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "pattern-analysis", content: scripts }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setResult(data.result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "오류가 발생했습니다");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(result);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-4xl">
      <Link
        href="/script-analysis"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4"
      >
        <ArrowLeft className="h-4 w-4" />
        대본분석
      </Link>

      <h1 className="text-3xl font-bold mb-2">대본 패턴 분석</h1>
      <p className="text-muted-foreground mb-6">
        여러 광고 대본을 입력하면 AI가 성공 패턴을 분석합니다. 대본 사이에 빈
        줄을 넣어 구분해주세요.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input */}
        <Card>
          <CardHeader>
            <CardTitle>광고 대본 입력</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder={`대본 1:\n이거 모르면 매달 10만원 손해...\n\n대본 2:\n3초만 투자하세요, 인생이 바뀝니다...\n\n대본 3:\n...`}
              value={scripts}
              onChange={(e) => setScripts(e.target.value)}
              rows={16}
              className="resize-none"
            />
            <Button
              onClick={handleSubmit}
              disabled={loading || !scripts.trim()}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  AI 분석 중...
                </>
              ) : (
                "패턴 분석"
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Output */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>분석 결과</CardTitle>
              {result && (
                <Button variant="ghost" size="sm" onClick={handleCopy}>
                  {copied ? (
                    <Check className="h-4 w-4 text-green-600" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {error && (
              <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
                {error}
              </div>
            )}
            {!result && !error && !loading && (
              <p className="text-muted-foreground text-center py-12">
                대본들을 입력하고 분석 버튼을 클릭하세요
              </p>
            )}
            {loading && (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            )}
            {result && (
              <div className="prose prose-sm max-w-none whitespace-pre-wrap text-sm leading-relaxed">
                {result}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
