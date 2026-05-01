"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Loader2, Plus, X, Instagram, Sparkles } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Image from "next/image";

type AdResult = {
  id: string;
  imageUrl: string;
  adCopy: { headline: string; subheadline: string };
  caption: string;
  hashtags: string[];
  status: string;
};

const TONE_OPTIONS = [
  { value: "신뢰감_있고_혜택_중심적", label: "신뢰감 · 혜택 강조" },
  { value: "감성적이고_따뜻한", label: "감성적 · 따뜻한" },
  { value: "긴박감_있고_한정혜택", label: "긴박감 · 한정 혜택" },
  { value: "유머러스하고_친근한", label: "유머러스 · 친근한" },
  { value: "프리미엄_고급스러운", label: "프리미엄 · 고급" },
];

export default function InstagramCreatePage() {
  const router = useRouter();
  const [serviceType, setServiceType] = useState("rental");
  const [productName, setProductName] = useState("");
  const [price, setPrice] = useState("");
  const [featureInput, setFeatureInput] = useState("");
  const [features, setFeatures] = useState<string[]>([]);
  const [tone, setTone] = useState("신뢰감_있고_혜택_중심적");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<AdResult | null>(null);
  const [editCaption, setEditCaption] = useState("");
  const [editHashtags, setEditHashtags] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const addFeature = () => {
    const v = featureInput.trim();
    if (v && !features.includes(v)) {
      setFeatures([...features, v]);
    }
    setFeatureInput("");
  };

  const removeFeature = (f: string) => setFeatures(features.filter((x) => x !== f));

  const handleGenerate = async () => {
    if (!productName.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    setUploadSuccess(false);

    try {
      const res = await fetch("/api/instagram", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ serviceType, productName, price, features, tone }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setResult(data);
      setEditCaption(data.caption || "");
      setEditHashtags(data.hashtags || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "오류가 발생했습니다");
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!result) return;
    setUploading(true);
    setUploadError("");

    const fullCaption = `${editCaption}\n\n${editHashtags.map((h) => `#${h}`).join(" ")}`;

    try {
      const res = await fetch("/api/instagram/upload", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: result.id, caption: fullCaption }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setUploadSuccess(true);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "업로드 실패");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-5xl">
      <Link
        href="/instagram"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4"
      >
        <ArrowLeft className="h-4 w-4" />
        인스타그램 광고
      </Link>

      <h1 className="text-3xl font-bold mb-2">광고 이미지 생성</h1>
      <p className="text-muted-foreground mb-6">
        제품 정보를 입력하면 AI가 광고 이미지와 카피를 자동 생성합니다
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 입력 폼 */}
        <Card>
          <CardHeader>
            <CardTitle>광고 정보 입력</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>서비스 유형</Label>
              <Select value={serviceType} onValueChange={(v) => v && setServiceType(v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="rental">렌탈 서비스</SelectItem>
                  <SelectItem value="internet">인터넷 서비스</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="productName">제품명 *</Label>
              <Input
                id="productName"
                placeholder="예: LG 퓨리케어 공기청정기, SK브로드밴드 인터넷"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
              />
            </div>

            <div>
              <Label htmlFor="price">가격 / 혜택 (선택)</Label>
              <Input
                id="price"
                placeholder="예: 월 29,900원, 6개월 무료, 설치비 0원"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
              />
            </div>

            <div>
              <Label>주요 특징</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="특징 입력 후 Enter"
                  value={featureInput}
                  onChange={(e) => setFeatureInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addFeature())}
                />
                <Button variant="outline" size="icon" onClick={addFeature}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              {features.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {features.map((f) => (
                    <Badge key={f} variant="secondary" className="gap-1 cursor-pointer" onClick={() => removeFeature(f)}>
                      {f} <X className="h-3 w-3" />
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            <div>
              <Label>광고 톤</Label>
              <Select value={tone} onValueChange={(v) => v && setTone(v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TONE_OPTIONS.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button
              onClick={handleGenerate}
              disabled={loading || !productName.trim()}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  이미지 생성 중... (20~30초)
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  광고 이미지 생성
                </>
              )}
            </Button>

            {error && (
              <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
                {error}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 미리보기 */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>미리보기</CardTitle>
            </CardHeader>
            <CardContent>
              {loading && (
                <div className="flex flex-col items-center justify-center py-16 gap-3">
                  <Loader2 className="h-10 w-10 animate-spin text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">AI가 이미지를 생성하고 있습니다...</p>
                </div>
              )}

              {!result && !loading && (
                <div className="flex items-center justify-center py-16 text-muted-foreground text-sm">
                  광고 정보를 입력하고 생성 버튼을 누르세요
                </div>
              )}

              {result && !loading && (
                <div className="space-y-3">
                  {/* 이미지 + 카피 오버레이 */}
                  <div className="relative aspect-square rounded-lg overflow-hidden bg-muted">
                    <Image
                      src={result.imageUrl}
                      alt="generated ad"
                      fill
                      className="object-cover"
                    />
                    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-4">
                      <p className="text-white font-bold text-xl leading-tight">
                        {result.adCopy?.headline}
                      </p>
                      <p className="text-white/90 text-sm mt-1">
                        {result.adCopy?.subheadline}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {result && (
            <Card>
              <CardHeader>
                <CardTitle>캡션 편집</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Textarea
                  value={editCaption}
                  onChange={(e) => setEditCaption(e.target.value)}
                  rows={4}
                  className="text-sm"
                />
                <div>
                  <Label className="text-xs text-muted-foreground mb-1 block">해시태그</Label>
                  <div className="flex flex-wrap gap-1">
                    {editHashtags.map((h) => (
                      <Badge key={h} variant="outline" className="text-xs cursor-pointer gap-1"
                        onClick={() => setEditHashtags(editHashtags.filter((x) => x !== h))}>
                        #{h} <X className="h-2 w-2" />
                      </Badge>
                    ))}
                  </div>
                </div>

                {uploadSuccess ? (
                  <div className="p-3 rounded-lg bg-green-50 text-green-700 text-sm font-medium">
                    인스타그램 업로드 완료!
                  </div>
                ) : (
                  <>
                    {uploadError && (
                      <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
                        {uploadError}
                      </div>
                    )}
                    <Button onClick={handleUpload} disabled={uploading} className="w-full">
                      {uploading ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          업로드 중...
                        </>
                      ) : (
                        <>
                          <Instagram className="h-4 w-4 mr-2" />
                          인스타그램에 업로드
                        </>
                      )}
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
