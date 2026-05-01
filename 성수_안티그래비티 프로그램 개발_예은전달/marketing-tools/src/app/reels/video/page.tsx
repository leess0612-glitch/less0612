"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Film, Type, Music, ImageIcon } from "lucide-react";
import Link from "next/link";

const tips = [
  {
    icon: Type,
    title: "텍스트 오버레이",
    description:
      "CapCut이나 InShot에서 대본의 핵심 문구를 화면에 텍스트로 표시하세요. 자막형 릴스가 가장 높은 조회수를 기록합니다.",
  },
  {
    icon: Film,
    title: "B-Roll 활용",
    description:
      "Pexels, Pixabay에서 무료 영상 소스를 다운받아 배경으로 사용하세요. 스마트폰 사용 장면, 채팅 화면 등이 효과적입니다.",
  },
  {
    icon: Music,
    title: "트렌딩 BGM",
    description:
      "각 플랫폼의 트렌딩 음악을 활용하세요. 인스타는 릴스 음악 라이브러리, 틱톡은 인기 사운드를 확인하세요.",
  },
  {
    icon: ImageIcon,
    title: "썸네일",
    description:
      "첫 프레임이 썸네일이 됩니다. 텍스트 + 감정적 이미지 조합으로 클릭율을 높이세요.",
  },
];

const tools = [
  {
    name: "CapCut",
    description: "무료 영상 편집, 자동 자막, 템플릿 제공",
    url: "https://www.capcut.com",
  },
  {
    name: "Canva",
    description: "릴스 템플릿, 썸네일 제작",
    url: "https://www.canva.com",
  },
  {
    name: "InShot",
    description: "모바일 영상 편집, 텍스트/스티커 추가",
    url: "https://inshot.com",
  },
  {
    name: "Runway ML",
    description: "AI 영상 생성, 배경 제거",
    url: "https://runwayml.com",
  },
  {
    name: "ElevenLabs",
    description: "AI 보이스오버, 한국어 TTS",
    url: "https://elevenlabs.io",
  },
];

export default function ReelsVideoPage() {
  return (
    <div className="max-w-4xl">
      <Link
        href="/reels"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4"
      >
        <ArrowLeft className="h-4 w-4" />
        릴스 광고 자동화
      </Link>

      <h1 className="text-3xl font-bold mb-2">영상 제작 가이드</h1>
      <p className="text-muted-foreground mb-6">
        생성된 대본을 영상으로 만들기 위한 팁과 도구를 안내합니다
      </p>

      <h2 className="text-xl font-semibold mb-4">제작 팁</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        {tips.map((tip) => (
          <Card key={tip.title}>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-primary/10">
                  <tip.icon className="h-5 w-5 text-primary" />
                </div>
                <CardTitle className="text-base">{tip.title}</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{tip.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <h2 className="text-xl font-semibold mb-4">추천 도구</h2>
      <div className="space-y-3">
        {tools.map((tool) => (
          <Card key={tool.name}>
            <CardContent className="flex items-center justify-between py-4">
              <div>
                <p className="font-medium">{tool.name}</p>
                <p className="text-sm text-muted-foreground">
                  {tool.description}
                </p>
              </div>
              <a
                href={tool.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary hover:underline"
              >
                바로가기
              </a>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
