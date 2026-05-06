"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { ArrowLeft, Loader2, Search, Sparkles, Upload, CheckCircle2, XCircle, Film, Mic } from "lucide-react";
import Link from "next/link";

type AnalysisResult = {
  id: string;
  title: string;
  platform: string;
  analysis: {
    adStructure: { hook: string; body: string; cta: string };
    scriptStyle: { tone: string; pacing: string; keywords: string[] };
    hooks: string[];
    targetAudience: string;
    summary: string;
  };
};

type GeneratedResult = {
  slideshow: { id: string; videoPath: string; caption: string } | null;
  voiceover: { id: string; videoPath: string; caption: string } | null;
  slideshowError: string | null;
  voiceoverError: string | null;
};

type UploadResults = Record<string, { success: boolean; id?: string; error?: string }>;
type GenType = "B" | "C" | "both";

const STEPS = ["1. 광고 분석", "2. 영상 생성", "3. 업로드"];
const PLATFORMS = [
  { id: "instagram", label: "Instagram Reels" },
  { id: "youtube", label: "YouTube Shorts" },
  { id: "tiktok", label: "TikTok" },
];
const GEN_TYPES: { value: GenType; label: string; desc: string; icon: typeof Film; time: string }[] = [
  { value: "B", label: "B타입 — 슬라이드쇼", desc: "이미지 4장 + 자막 영상", icon: Film, time: "약 3~4분" },
  { value: "C", label: "C타입 — 나레이션", desc: "AI 목소리 + 자막 영상", icon: Mic, time: "약 2~3분" },
  { value: "both", label: "B + C 동시", desc: "두 가지 모두 생성", icon: Sparkles, time: "약 4~5분" },
];

export default function AdAnalyzerCreatePage() {
  const [step, setStep] = useState(0);

  // Step 1
  const [url, setUrl] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState("");
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);

  // Step 2
  const [serviceType, setServiceType] = useState("rental");
  const [productName, setProductName] = useState("");
  const [price, setPrice] = useState("");
  const [genType, setGenType] = useState<GenType>("B");
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState("");
  const [generated, setGenerated] = useState<GeneratedResult | null>(null);
  const [selectedAdId, setSelectedAdId] = useState<string | null>(null);

  // Step 3
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(["instagram"]);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState<UploadResults | null>(null);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setAnalyzeError("");
    try {
      const res = await fetch("/api/ad-analyzer/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setAnalysis(data);
      setStep(1);
    } catch (err) {
      setAnalyzeError(err instanceof Error ? err.message : "분석 실패");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleGenerate = async () => {
    if (!analysis) return;
    setGenerating(true);
    setGenerateError("");
    setGenerated(null);
    try {
      const res = await fetch("/api/ad-analyzer/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ analysisId: analysis.id, serviceType, productName, price, type: genType }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setGenerated(data);
      setSelectedAdId(data.slideshow?.id ?? data.voiceover?.id ?? null);
      setStep(2);
    } catch (err) {
      setGenerateError(err instanceof Error ? err.message : "생성 실패");
    } finally {
      setGenerating(false);
    }
  };

  const togglePlatform = (id: string) =>
    setSelectedPlatforms((p) => p.includes(id) ? p.filter((x) => x !== id) : [...p, id]);

  const handleUpload = async () => {
    if (!selectedAdId || selectedPlatforms.length === 0) return;
    setUploading(true);
    const fullCaption = uploadTitle || "광고";
    try {
      const res = await fetch("/api/ad-analyzer/upload-platforms", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ generatedAdId: selectedAdId, platforms: selectedPlatforms, title: fullCaption }),
      });
      setUploadResults(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const selectedGenInfo = GEN_TYPES.find((g) => g.value === genType)!;

  return (
    <div className="max-w-4xl">
      <Link href="/ad-analyzer" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft className="h-4 w-4" />광고 분석기
      </Link>
      <h1 className="text-3xl font-bold mb-2">광고 분석 → 생성 → 업로드</h1>
      <p className="text-muted-foreground mb-6">경쟁사/참고 광고를 분석해 나만의 광고를 자동 생성합니다</p>

      {/* 스텝 표시 */}
      <div className="flex items-center gap-2 mb-8">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
              i === step ? "bg-primary text-primary-foreground" :
              i < step ? "bg-green-100 text-green-700" : "bg-muted text-muted-foreground"
            }`}>
              {i < step && <CheckCircle2 className="h-3.5 w-3.5" />}{s}
            </div>
            {i < STEPS.length - 1 && <div className="h-px w-6 bg-border" />}
          </div>
        ))}
      </div>

      {/* STEP 0: URL 입력 */}
      {step === 0 && (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Search className="h-5 w-5" />광고 URL 분석</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>YouTube 또는 Instagram URL</Label>
              <Input
                placeholder="https://www.youtube.com/watch?v=... 또는 https://www.instagram.com/reel/..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && url.trim() && handleAnalyze()}
              />
              <p className="text-xs text-muted-foreground mt-1">자막이 있는 YouTube 영상일수록 분석 품질이 높습니다</p>
            </div>
            {analyzeError && <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{analyzeError}</div>}
            <Button onClick={handleAnalyze} disabled={analyzing || !url.trim()} className="w-full">
              {analyzing ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />분석 중...</> : <><Search className="h-4 w-4 mr-2" />광고 분석 시작</>}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* STEP 1: 분석 결과 + 생성 설정 */}
      {step === 1 && analysis && (
        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle>분석 결과: {analysis.title || analysis.platform}</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div className="p-3 bg-muted rounded-lg text-sm">{analysis.analysis.summary}</div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div><span className="font-medium">톤: </span>{analysis.analysis.scriptStyle?.tone}</div>
                <div><span className="font-medium">타겟: </span>{analysis.analysis.targetAudience}</div>
                <div><span className="font-medium">도입부: </span>{analysis.analysis.adStructure?.hook}</div>
                <div><span className="font-medium">CTA: </span>{analysis.analysis.adStructure?.cta}</div>
              </div>
              <div>
                <p className="text-sm font-medium mb-1">후킹 문구 패턴</p>
                <div className="flex flex-wrap gap-1">
                  {(analysis.analysis.hooks || []).map((h, i) => (
                    <Badge key={i} variant="secondary" className="text-xs">{h}</Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><Sparkles className="h-5 w-5" />광고 생성 설정</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>서비스 유형</Label>
                  <Select value={serviceType} onValueChange={(v) => v && setServiceType(v)}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="rental">렌탈 서비스</SelectItem>
                      <SelectItem value="internet">인터넷 서비스</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>가격 / 혜택</Label>
                  <Input placeholder="예: 월 29,900원, 설치비 0원" value={price} onChange={(e) => setPrice(e.target.value)} />
                </div>
              </div>
              <div>
                <Label>제품명 *</Label>
                <Input placeholder="예: LG 퓨리케어 공기청정기" value={productName} onChange={(e) => setProductName(e.target.value)} />
              </div>

              {/* 생성 타입 선택 */}
              <div>
                <Label className="mb-2 block">생성 타입 선택</Label>
                <div className="grid grid-cols-3 gap-2">
                  {GEN_TYPES.map((g) => (
                    <button
                      key={g.value}
                      onClick={() => setGenType(g.value)}
                      className={`p-3 rounded-lg border text-left transition-all ${
                        genType === g.value ? "border-primary bg-primary/5 ring-1 ring-primary" : "border-border hover:border-primary/50"
                      }`}
                    >
                      <div className="flex items-center gap-1.5 mb-1">
                        <g.icon className="h-3.5 w-3.5 text-primary" />
                        <span className="text-xs font-semibold">{g.label}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">{g.desc}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{g.time}</p>
                    </button>
                  ))}
                </div>
              </div>

              <div className="p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
                <strong>{selectedGenInfo.label}</strong> 선택됨 — {selectedGenInfo.time} 소요됩니다. 생성 중 페이지를 닫지 마세요.
              </div>

              {generateError && <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">{generateError}</div>}

              <Button onClick={handleGenerate} disabled={generating || !productName.trim()} className="w-full">
                {generating ? (
                  <><Loader2 className="h-4 w-4 mr-2 animate-spin" />생성 중... ({selectedGenInfo.time} 소요)</>
                ) : (
                  <><Sparkles className="h-4 w-4 mr-2" />{selectedGenInfo.label} 생성</>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* STEP 2: 결과 + 업로드 */}
      {step === 2 && generated && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* B타입 */}
            {(generated.slideshow || generated.slideshowError) && (
              <Card className={`cursor-pointer transition-all ${selectedAdId === generated.slideshow?.id ? "ring-2 ring-primary" : ""}`}
                onClick={() => generated.slideshow && setSelectedAdId(generated.slideshow.id)}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base flex items-center gap-2"><Film className="h-4 w-4" />B타입 — 슬라이드쇼</CardTitle>
                    {generated.slideshow ? <Badge variant="secondary">생성완료</Badge> : <Badge variant="destructive">실패</Badge>}
                  </div>
                </CardHeader>
                <CardContent>
                  {generated.slideshow ? (
                    <>
                      <video src={generated.slideshow.videoPath} controls className="w-full rounded-lg aspect-square object-cover" />
                      <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{generated.slideshow.caption}</p>
                    </>
                  ) : (
                    <div className="p-3 text-sm text-destructive bg-destructive/10 rounded">{generated.slideshowError}</div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* C타입 */}
            {(generated.voiceover || generated.voiceoverError) && (
              <Card className={`cursor-pointer transition-all ${selectedAdId === generated.voiceover?.id ? "ring-2 ring-primary" : ""}`}
                onClick={() => generated.voiceover && setSelectedAdId(generated.voiceover.id)}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base flex items-center gap-2"><Mic className="h-4 w-4" />C타입 — 나레이션</CardTitle>
                    {generated.voiceover ? <Badge variant="secondary">생성완료</Badge> : <Badge variant="destructive">실패</Badge>}
                  </div>
                </CardHeader>
                <CardContent>
                  {generated.voiceover ? (
                    <>
                      <video src={generated.voiceover.videoPath} controls className="w-full rounded-lg aspect-square object-cover" />
                      <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{generated.voiceover.caption}</p>
                    </>
                  ) : (
                    <div className="p-3 text-sm text-destructive bg-destructive/10 rounded">{generated.voiceoverError}</div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>

          {/* 다른 타입 추가 생성 버튼 */}
          <div className="flex gap-2">
            {!generated.slideshow && (
              <Button variant="outline" size="sm" onClick={() => { setGenType("B"); setStep(1); }}>
                <Film className="h-3.5 w-3.5 mr-1" />B타입도 생성하기
              </Button>
            )}
            {!generated.voiceover && (
              <Button variant="outline" size="sm" onClick={() => { setGenType("C"); setStep(1); }}>
                <Mic className="h-3.5 w-3.5 mr-1" />C타입도 생성하기
              </Button>
            )}
          </div>

          {/* 업로드 */}
          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><Upload className="h-5 w-5" />업로드 설정</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>영상 제목 (YouTube용)</Label>
                <Input placeholder="예: LG 퓨리케어 렌탈 월 29,900원 혜택" value={uploadTitle} onChange={(e) => setUploadTitle(e.target.value)} />
              </div>
              <div>
                <Label className="mb-2 block">업로드 플랫폼</Label>
                <div className="flex gap-3 flex-wrap">
                  {PLATFORMS.map((p) => (
                    <button key={p.id} onClick={() => togglePlatform(p.id)}
                      className={`px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${
                        selectedPlatforms.includes(p.id) ? "bg-primary text-primary-foreground border-primary" : "border-border text-muted-foreground hover:border-primary"
                      }`}>
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              {uploadResults ? (
                <div className="space-y-2">
                  {Object.entries(uploadResults).map(([platform, result]) => (
                    <div key={platform} className={`flex items-center gap-2 p-3 rounded-lg text-sm ${result.success ? "bg-green-50 text-green-700" : "bg-destructive/10 text-destructive"}`}>
                      {result.success ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                      <span className="font-medium capitalize">{platform}</span>
                      <span>{result.success ? `완료 (ID: ${result.id})` : result.error}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <Button onClick={handleUpload} disabled={uploading || !selectedAdId || selectedPlatforms.length === 0} className="w-full">
                  {uploading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />업로드 중...</> : <><Upload className="h-4 w-4 mr-2" />선택한 플랫폼에 업로드</>}
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
