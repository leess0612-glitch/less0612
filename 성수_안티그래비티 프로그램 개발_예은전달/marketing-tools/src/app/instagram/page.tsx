"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Plus, Trash2, Camera, Loader2 } from "lucide-react";
import Link from "next/link";
import Image from "next/image";

type Ad = {
  id: string;
  serviceType: string;
  productName: string;
  price: string | null;
  imageUrl: string | null;
  adCopy: { headline: string; subheadline: string } | null;
  caption: string | null;
  hashtags: string[];
  status: string;
  postedAt: string | null;
  createdAt: string;
};

const STATUS_LABEL: Record<string, { label: string; variant: "default" | "secondary" | "outline" }> = {
  draft: { label: "초안", variant: "outline" },
  generated: { label: "생성완료", variant: "secondary" },
  uploaded: { label: "업로드됨", variant: "default" },
};

export default function InstagramPage() {
  const [ads, setAds] = useState<Ad[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/instagram")
      .then((r) => r.json())
      .then(setAds)
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("이 광고를 삭제하시겠습니까?")) return;
    setDeletingId(id);
    await fetch(`/api/instagram?id=${id}`, { method: "DELETE" });
    setAds(ads.filter((a) => a.id !== id));
    setDeletingId(null);
  };

  const generated = ads.filter((a) => a.status === "generated").length;
  const uploaded = ads.filter((a) => a.status === "uploaded").length;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">인스타그램 광고 자동화</h1>
          <p className="text-muted-foreground mt-1">렌탈/인터넷 광고 이미지 생성 및 업로드</p>
        </div>
        <Link href="/instagram/create">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            새 광고 만들기
          </Button>
        </Link>
      </div>

      {/* 통계 */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {[
          { label: "전체 광고", value: ads.length },
          { label: "생성 완료", value: generated },
          { label: "업로드됨", value: uploaded },
        ].map((stat) => (
          <Card key={stat.label}>
            <CardContent className="pt-6">
              <p className="text-2xl font-bold">{stat.value}</p>
              <p className="text-sm text-muted-foreground">{stat.label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 광고 목록 */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : ads.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <Camera className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>아직 생성된 광고가 없습니다</p>
          <Link href="/instagram/create">
            <Button variant="outline" className="mt-4">첫 광고 만들기</Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {ads.map((ad) => {
            const statusInfo = STATUS_LABEL[ad.status] || STATUS_LABEL.draft;
            return (
              <Card key={ad.id} className="overflow-hidden">
                {/* 이미지 썸네일 */}
                <div className="relative aspect-square bg-muted">
                  {ad.imageUrl ? (
                    <Image src={ad.imageUrl} alt={ad.productName} fill className="object-cover" />
                  ) : (
                    <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                      이미지 없음
                    </div>
                  )}
                  {ad.imageUrl && ad.adCopy && (
                    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-3">
                      <p className="text-white font-bold text-sm leading-tight">{ad.adCopy.headline}</p>
                      <p className="text-white/80 text-xs mt-0.5">{ad.adCopy.subheadline}</p>
                    </div>
                  )}
                </div>

                <CardContent className="p-3">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="min-w-0">
                      <p className="font-medium text-sm truncate">{ad.productName}</p>
                      <p className="text-xs text-muted-foreground">
                        {ad.serviceType === "rental" ? "렌탈" : "인터넷"} ·{" "}
                        {new Date(ad.createdAt).toLocaleDateString("ko-KR")}
                      </p>
                    </div>
                    <Badge variant={statusInfo.variant} className="text-xs shrink-0">
                      {statusInfo.label}
                    </Badge>
                  </div>

                  {ad.status === "uploaded" && ad.postedAt && (
                    <p className="text-xs text-green-600 mb-2">
                      업로드: {new Date(ad.postedAt).toLocaleDateString("ko-KR")}
                    </p>
                  )}

                  <div className="flex gap-2">
                    {ad.status === "generated" && (
                      <Link href={`/instagram/create`} className="flex-1">
                        <Button variant="outline" size="sm" className="w-full text-xs">
                          <Camera className="h-3 w-3 mr-1" />
                          업로드
                        </Button>
                      </Link>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive"
                      disabled={deletingId === ad.id}
                      onClick={() => handleDelete(ad.id)}
                    >
                      {deletingId === ad.id ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <Trash2 className="h-3 w-3" />
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
