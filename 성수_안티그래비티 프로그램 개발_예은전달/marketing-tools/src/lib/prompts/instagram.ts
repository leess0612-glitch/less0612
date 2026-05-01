export const INSTAGRAM_AD_COPY_SYSTEM = `당신은 렌탈/인터넷 서비스 전문 광고 카피라이터입니다.
주어진 제품 정보를 바탕으로 인스타그램 광고에 적합한 짧고 임팩트 있는 카피를 생성합니다.

응답은 반드시 아래 JSON 형식으로만 출력하세요. 다른 텍스트는 절대 포함하지 마세요:
{
  "headline": "헤드라인 (15자 이내, 핵심 혜택 강조)",
  "subheadline": "서브 헤드라인 (30자 이내, 구체적 혜택)",
  "caption": "인스타 캡션 (150자 이내, 이모지 2-3개 포함, 행동 유도 문구 포함)",
  "hashtags": ["해시태그1", "해시태그2"],
  "imagePrompt": "DALL-E image prompt in English (clean Korean ad style, product-focused, no text in image)"
}

해시태그는 최대 15개, #기호 없이 단어만 입력하세요.
imagePrompt는 반드시 영어로 작성하고, 한국 광고 스타일의 깔끔한 제품 이미지를 묘사하세요.`;

export function buildAdUserMessage(params: {
  serviceType: string;
  productName: string;
  price?: string;
  features: string[];
  tone?: string;
}): string {
  const { serviceType, productName, price, features, tone } = params;
  const serviceLabel = serviceType === "rental" ? "렌탈 서비스" : "인터넷 서비스";
  return `서비스 유형: ${serviceLabel}
제품명: ${productName}
${price ? `가격/혜택: ${price}` : ""}
주요 특징: ${features.filter(Boolean).join(", ")}
광고 톤: ${tone || "신뢰감 있고 혜택 중심적"}

위 정보로 인스타그램 광고 카피와 이미지 프롬프트를 생성해주세요.`;
}
