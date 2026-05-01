"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Loader2, Copy, Check } from "lucide-react";
import Link from "next/link";

export default function BlogToScriptPage() {
  const [blogContent, setBlogContent] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const handleSubmit = async () => {
    if (!blogContent.trim()) return;
    setLoading(true);
    setError("");
    setResult("");

    try {
      const res = await fetch("/api/script-analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "blog-to-script", content: blogContent }),
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

      <h1 className="text-3xl font-bold mb-2">블로그 → 광고 대본 변환</h1>
      <p className="text-muted-foreground mb-6">
        블로그 글을 붙여넣으면 AI가 숏폼 광고 대본으로 변환합니다
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input */}
        <Card>
          <CardHeader>
            <CardTitle>블로그 원문</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="블로그 글을 붙여넣으세요..."
              value={blogContent}
              onChange={(e) => setBlogContent(e.target.value)}
              rows={16}
              className="resize-none"
            />
            <Button
              onClick={handleSubmit}
              disabled={loading || !blogContent.trim()}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  AI 변환 중...
                </>
              ) : (
                "대본으로 변환"
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Output */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>생성된 대본</CardTitle>
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
                블로그 글을 입력하고 변환 버튼을 클릭하세요
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
