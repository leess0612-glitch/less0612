"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ArrowLeft, Save } from "lucide-react";
import Link from "next/link";

interface ReelsProject {
  id: string;
  title: string;
  platform: string;
  status: string;
  uploadId: string | null;
  metrics: {
    views: number;
    likes: number;
    comments: number;
    shares: number;
    ctr: number;
  } | null;
  createdAt: string;
}

const platformLabels: Record<string, string> = {
  instagram: "Instagram",
  tiktok: "TikTok",
  youtube: "YouTube",
};

export default function ReelsTrackingPage() {
  const [projects, setProjects] = useState<ReelsProject[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [views, setViews] = useState("");
  const [likes, setLikes] = useState("");
  const [comments, setComments] = useState("");
  const [shares, setShares] = useState("");
  const [ctr, setCtr] = useState("");

  const fetchProjects = useCallback(async () => {
    const res = await fetch("/api/reels");
    const data = await res.json();
    setProjects(data);
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleSaveMetrics = async () => {
    if (!selectedId) return;

    await fetch("/api/reels", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "update-metrics",
        id: selectedId,
        metrics: {
          views: parseInt(views) || 0,
          likes: parseInt(likes) || 0,
          comments: parseInt(comments) || 0,
          shares: parseInt(shares) || 0,
          ctr: parseFloat(ctr) || 0,
        },
      }),
    });

    setViews("");
    setLikes("");
    setComments("");
    setShares("");
    setCtr("");
    setSelectedId("");
    fetchProjects();
  };

  const uploadedProjects = projects.filter(
    (p) => p.status === "uploaded" || p.status === "tracking"
  );
  const trackedProjects = projects.filter((p) => p.metrics);

  const fmt = (n: number) => n.toLocaleString("ko-KR");

  // Summary stats
  const totalViews = trackedProjects.reduce(
    (s, p) => s + (p.metrics?.views ?? 0),
    0
  );
  const totalLikes = trackedProjects.reduce(
    (s, p) => s + (p.metrics?.likes ?? 0),
    0
  );
  const avgCtr =
    trackedProjects.length > 0
      ? trackedProjects.reduce((s, p) => s + (p.metrics?.ctr ?? 0), 0) /
        trackedProjects.length
      : 0;

  return (
    <div className="max-w-5xl">
      <Link
        href="/reels"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4"
      >
        <ArrowLeft className="h-4 w-4" />
        릴스 광고 자동화
      </Link>

      <h1 className="text-3xl font-bold mb-2">성과 추적</h1>
      <p className="text-muted-foreground mb-6">
        업로드한 콘텐츠의 성과 지표를 입력하고 추적합니다
      </p>

      {/* Summary */}
      {trackedProjects.length > 0 && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">
                총 조회수
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{fmt(totalViews)}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">
                총 좋아요
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{fmt(totalLikes)}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground">
                평균 CTR
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{avgCtr.toFixed(2)}%</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Metrics Input */}
      {uploadedProjects.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>성과 지표 입력</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="col-span-2 md:col-span-3">
                <Label>프로젝트 선택</Label>
                <Select value={selectedId} onValueChange={(v) => v && setSelectedId(v)}>
                  <SelectTrigger>
                    <SelectValue placeholder="프로젝트를 선택하세요" />
                  </SelectTrigger>
                  <SelectContent>
                    {uploadedProjects.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.title} ({platformLabels[p.platform]})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="views">조회수</Label>
                <Input
                  id="views"
                  type="number"
                  placeholder="0"
                  value={views}
                  onChange={(e) => setViews(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="likes">좋아요</Label>
                <Input
                  id="likes"
                  type="number"
                  placeholder="0"
                  value={likes}
                  onChange={(e) => setLikes(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="comments">댓글</Label>
                <Input
                  id="comments"
                  type="number"
                  placeholder="0"
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="shares">공유</Label>
                <Input
                  id="shares"
                  type="number"
                  placeholder="0"
                  value={shares}
                  onChange={(e) => setShares(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="ctr">CTR (%)</Label>
                <Input
                  id="ctr"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={ctr}
                  onChange={(e) => setCtr(e.target.value)}
                />
              </div>
              <div className="flex items-end">
                <Button onClick={handleSaveMetrics} disabled={!selectedId}>
                  <Save className="h-4 w-4 mr-2" />
                  저장
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tracking Table */}
      <Card>
        <CardHeader>
          <CardTitle>성과 현황</CardTitle>
        </CardHeader>
        <CardContent>
          {trackedProjects.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">
              아직 추적 중인 콘텐츠가 없습니다
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>제목</TableHead>
                  <TableHead>플랫폼</TableHead>
                  <TableHead className="text-right">조회수</TableHead>
                  <TableHead className="text-right">좋아요</TableHead>
                  <TableHead className="text-right">댓글</TableHead>
                  <TableHead className="text-right">공유</TableHead>
                  <TableHead className="text-right">CTR</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {trackedProjects.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell className="font-medium">{p.title}</TableCell>
                    <TableCell>
                      {platformLabels[p.platform] || p.platform}
                    </TableCell>
                    <TableCell className="text-right">
                      {fmt(p.metrics?.views ?? 0)}
                    </TableCell>
                    <TableCell className="text-right">
                      {fmt(p.metrics?.likes ?? 0)}
                    </TableCell>
                    <TableCell className="text-right">
                      {fmt(p.metrics?.comments ?? 0)}
                    </TableCell>
                    <TableCell className="text-right">
                      {fmt(p.metrics?.shares ?? 0)}
                    </TableCell>
                    <TableCell className="text-right">
                      {(p.metrics?.ctr ?? 0).toFixed(2)}%
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
