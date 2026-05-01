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
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Plus, ExternalLink } from "lucide-react";
import Link from "next/link";

interface ReelsProject {
  id: string;
  title: string;
  platform: string;
  status: string;
  uploadId: string | null;
  createdAt: string;
}

const platformLabels: Record<string, string> = {
  instagram: "Instagram",
  tiktok: "TikTok",
  youtube: "YouTube",
};

const statusLabels: Record<string, string> = {
  draft: "초안",
  script_ready: "대본 완료",
  uploaded: "업로드됨",
  tracking: "추적 중",
};

export default function ReelsUploadPage() {
  const [projects, setProjects] = useState<ReelsProject[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [uploadId, setUploadId] = useState("");
  const [platform, setPlatform] = useState("instagram");

  const fetchProjects = useCallback(async () => {
    const res = await fetch("/api/reels");
    const data = await res.json();
    setProjects(data);
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleSaveUpload = async () => {
    if (!selectedId || !uploadId) return;

    await fetch("/api/reels", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "save-upload",
        id: selectedId,
        uploadId,
        platform,
      }),
    });

    setUploadId("");
    setSelectedId("");
    fetchProjects();
  };

  const scriptReadyProjects = projects.filter(
    (p) => p.status === "script_ready"
  );

  return (
    <div className="max-w-4xl">
      <Link
        href="/reels"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4"
      >
        <ArrowLeft className="h-4 w-4" />
        릴스 광고 자동화
      </Link>

      <h1 className="text-3xl font-bold mb-2">업로드 관리</h1>
      <p className="text-muted-foreground mb-6">
        영상을 업로드한 후 게시물 ID/URL을 등록하여 추적합니다
      </p>

      {scriptReadyProjects.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>업로드 정보 등록</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>프로젝트 선택</Label>
              <Select value={selectedId} onValueChange={(v) => v && setSelectedId(v)}>
                <SelectTrigger>
                  <SelectValue placeholder="프로젝트를 선택하세요" />
                </SelectTrigger>
                <SelectContent>
                  {scriptReadyProjects.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.title} ({platformLabels[p.platform]})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>업로드 플랫폼</Label>
              <Select value={platform} onValueChange={(v) => v && setPlatform(v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="instagram">Instagram</SelectItem>
                  <SelectItem value="tiktok">TikTok</SelectItem>
                  <SelectItem value="youtube">YouTube</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="uploadId">게시물 ID 또는 URL</Label>
              <Input
                id="uploadId"
                placeholder="게시물 URL 또는 ID를 입력하세요"
                value={uploadId}
                onChange={(e) => setUploadId(e.target.value)}
              />
            </div>

            <Button
              onClick={handleSaveUpload}
              disabled={!selectedId || !uploadId}
            >
              <Plus className="h-4 w-4 mr-2" />
              등록
            </Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>업로드 현황</CardTitle>
        </CardHeader>
        <CardContent>
          {projects.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">
              아직 프로젝트가 없습니다.{" "}
              <Link href="/reels/script" className="text-primary hover:underline">
                대본 생성
              </Link>
              부터 시작하세요.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>제목</TableHead>
                  <TableHead>플랫폼</TableHead>
                  <TableHead>상태</TableHead>
                  <TableHead>게시물</TableHead>
                  <TableHead>생성일</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {projects.map((project) => (
                  <TableRow key={project.id}>
                    <TableCell className="font-medium">
                      {project.title}
                    </TableCell>
                    <TableCell>
                      {platformLabels[project.platform] || project.platform}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          project.status === "uploaded" ||
                          project.status === "tracking"
                            ? "default"
                            : "secondary"
                        }
                      >
                        {statusLabels[project.status] || project.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {project.uploadId ? (
                        project.uploadId.startsWith("http") ? (
                          <a
                            href={project.uploadId}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-primary hover:underline text-sm"
                          >
                            보기 <ExternalLink className="h-3 w-3" />
                          </a>
                        ) : (
                          <span className="text-sm">{project.uploadId}</span>
                        )
                      ) : (
                        <span className="text-muted-foreground text-sm">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(project.createdAt).toLocaleDateString("ko-KR")}
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
