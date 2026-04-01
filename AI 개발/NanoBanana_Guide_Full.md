# [Ai싱크클럽] 나노바나나PRO 가이드북 (Full Version)

> **이 가이드북에 대하여**
> 이 문서는 노션 원본 페이지의 모든 내용을 빠짐없이 크롤링하여 통합한 Full-Text 버전입니다.
> 각 Part별 상세 설명, 프롬프트 예시, 실패/성공 비교, 워크플로우 단계가 모두 포함되어 있습니다.

---

## 📖 전체 목차
1. **Part 0**: 지금 가장 핫한 나노바나나 활용법 21가지
2. **Part 1**: 이미지 생성
3. **Part 2**: 이미지 편집
4. **Part 3**: 비즈니스 & 마케팅
5. **Part 4**: 교육 & 학습
6. **Part 5**: 창작 & 엔터테인먼트
7. **Part 6**: 고급 활용
8. **Part 7**: 추가 활용 사례
9. **부록**: 프롬프트 작성 공식

---

## Part 0. 지금 가장 핫한 나노바나나 활용법 21가지
“이런 것까지 된다고?” 실무자와 크리에이터를 위한 실전 프롬프트 사례집

### 1. 비즈니스 & 문서 자동화

#### 1.1. 복잡한 프로세스를 한눈에, 도식화 & 흐름도
*   **상황**: 회의 자료, 보고서, 제안서에 들어갈 복잡한 업무 프로세스나 시스템 구조를 시각적으로 표현해야 할 때
*   **팁**: `flowchart`, `diagram`, `nodes`, `arrows` 같은 키워드를 활용하고, 각 단계의 내용을 명확히 지정하는 것이 중요합니다.
*   **프롬프트 예시**:
    > A flowchart diagram illustrating the process of 'Online Order Fulfillment'. It starts with 'Customer Places Order', moves to 'Payment Confirmation', then splits into 'Check Inventory'. If 'In Stock', it goes to 'Package & Ship', then 'Send Tracking Info', and ends with 'Order Complete'. If 'Out of Stock', it goes to 'Notify Customer' and 'Offer Alternatives'. Use clean, simple nodes and clear arrows. Minimalist, corporate blue and grey color palette.

#### 1.2. 논문과 보고서의 퀄리티를 높이는, 전문 삽화
*   **상황**: 학위 논문, 기술 보고서, 연구 발표 자료에 텍스트만으로는 설명하기 어려운 개념이나 실험 과정을 시각적으로 보여줘야 할 때
*   **팁**: `scientific illustration`, `academic paper diagram`, `cross-section view` 등의 전문 용어를 사용하고, 라벨링을 위한 공간을 요청(`with space for labels`)하는 것이 좋습니다.
*   **프롬프트 예시**:
    > Scientific illustration for a biology thesis, showing the process of CRISPR-Cas9 gene editing. The diagram should clearly depict the Cas9 protein, guide RNA, target DNA strand, and the moment of the DNA cut. The style should be clean, detailed, and professional, suitable for an academic publication. Include pointers and space for labels.

#### 1.3. 설득력을 더하는 비교표 & 시장 분석
*   **상황**: 경쟁사 제품과 우리 제품의 장단점을 비교하거나, 전체 시장(TAM), 유효 시장(SAM), 수익 시장(SOM)을 시각적으로 분석하여 발표해야 할 때
*   **팁**: `comparison table`, `infographic chart`, `venn diagram` 등을 활용하고, 각 항목의 데이터를 명확히 제시하세요.
*   **프롬프트 예시**:
    > Infographic chart showing a market analysis using the TAM, SAM, SOM model. Depict three concentric circles. The largest circle, labeled 'TAM (Total Addressable Market) - Global Smartphone Market $500B', contains a smaller circle 'SAM (Serviceable Available Market) - Korean Smartphone Market $20B', which in turn contains the smallest circle 'SOM (Serviceable Obtainable Market) - Our Target Segment $1B'. Use modern, flat design with corporate colors and clear typography.

#### 1.4. 한 장으로 끝내는, 상세페이지 기획안
*   **상황**: 새로운 제품이나 서비스의 온라인 판매를 위해 상세페이지 전체의 흐름과 구성을 시각적으로 기획하고 싶을 때
*   **팁**: `long scrollable page`, `UI design`, `wireframe` 키워드를 사용하고, '히어로 섹션', '주요 기능', '고객 후기' 등 포함될 모든 섹션을 순서대로 나열하세요.
*   **프롬프트 예시**:
    > A long, scrollable, and visually appealing product detail page for a new organic skincare serum. The page should include a hero section with a beautiful product shot, sections for key ingredients with illustrations, before-and-after comparison photos, customer testimonials with portraits, a 'how to use' guide with step-by-step diagrams, and a final call-to-action button. The overall design should be clean, minimalist, and use a palette of green, white, and gold. Infographic style, UI design.

#### 1.5. 아이디어를 현실로, 행사 부스 디자인 시안
*   **상황**: 다가오는 박람회나 행사를 위해 우리 회사 부스를 어떻게 꾸밀지 3D 시안으로 미리 확인하고 싶을 때
*   **팁**: `3D render`, `exhibition booth design`, `isometric view`를 활용하고, 회사 로고, 제품 디스플레이, 상담 공간 등의 요소를 구체적으로 명시하세요.
*   **프롬프트 예시**:
    > 3D render of an exhibition booth design for a tech startup. The booth (10x10 meters) should have a large backlit logo, a central product display table with interactive screens, a comfortable seating area for meetings, and dynamic LED strip lighting. The style should be modern, sleek, and inviting. Isometric view. + 간판에는 "Ai싱크클럽" 이라고 적혀있다

### 2. 디자인 & 마케팅

#### 2.1. 시선을 사로잡는, SNS 광고 & 축제 포스터
*   **상황**: 인스타그램, 페이스북에 올릴 이벤트 광고 이미지나 대학교 축제 포스터를 빠르고 감각적으로 만들어야 할 때
*   **팁**: `Instagram ad post`, `music festival poster` 등 매체와 목적을 명시하고, `bold typography`, `vibrant colors`, `eye-catching` 같은 디자인 키워드를 사용하세요.
*   **프롬프트 예시**:
    > An eye-catching Instagram ad post for a 'Summer Sale - 50% OFF' event. The image should feature trendy summer fashion items like sunglasses and sandals on a vibrant, colorful background. Use bold, playful typography for the text 'Summer Sale'. 1:1 square format.

#### 2.2. 컨셉을 한눈에, 무드보드 기반 생성
*   **상황**: 특정 컨셉(예: '편안한 주말 아침')에 맞는 여러 이미지들을 조합하여 하나의 통일된 톤앤매너를 가진 이미지를 만들고 싶을 때
*   **팁**: `mood board` 키워드와 함께 원하는 컨셉을 구성하는 요소들(이미지, 색상, 텍스처)을 나열하세요.
*   **프롬프트 예시**:
    > Generate an image based on a mood board for a 'Cozy Weekend Morning'. The mood board includes: a cup of steaming coffee, a soft knitted blanket, an open book, warm sunlight filtering through a window, and a palette of beige, cream, and soft brown. The final image should evoke a feeling of peace and comfort.

#### 2.3. 영화의 한 장면처럼, 스토리보드 제작
*   **상황**: 단편 영화, 광고, 유튜브 영상의 주요 장면들을 미리 시각화하여 전체적인 흐름을 파악하고 싶을 때
*   **팁**: `storyboard`, `sequence of 4 panels` 처럼 패널 수를 지정하고, 각 패널의 장면을 번호와 함께 구체적으로 묘사하세요.
*   **프롬프트 예시**:
    > Storyboard with a sequence of 4 panels for a short film scene. Panel 1: A young woman discovers an old, dusty book in an attic. Panel 2: Close-up on her surprised face as she opens the book. Panel 3: The book emits a magical glow. Panel 4: She looks up, her face illuminated by the light, with a sense of wonder. Cinematic, dramatic lighting.

#### 2.4. 우리 아이를 위한, 색칠공부 도안
*   **상황**: 아이들이 좋아하는 동물이나 캐릭터로 세상에 하나뿐인 색칠공부 책을 만들어주고 싶을 때
*   **팁**: `coloring book page for children`, `simple outlines`, `thick lines`, `no shading` 키워드가 핵심입니다.
*   **프롬프트 예시**:
    > Coloring book page for children, featuring a friendly dinosaur family (a father, mother, and a baby dinosaur) having a picnic in a prehistoric landscape. The image should have simple, clear, and thick outlines, with large areas for coloring. No shading or complex details. White background.

#### 2.5. 나만의 이모티콘 만들기, 카카오톡 이모티콘
*   **상황**: 내 캐릭터나 아이디어를 카카오톡 이모티콘으로 만들어 출시하고 싶을 때, 다양한 감정 표현 시안을 제작합니다.
*   **팁**: `a set of 6 KakaoTalk emoticons`, `chibi character`, `simple and expressive` 키워드를 사용하고, '웃음', '울음', '화남' 등 원하는 감정 표현을 명시하세요.
*   **프롬프트 예시**:
    > AI싱크클럽 로고를 적은 파란색 캡모자를 쓴 테디베어 캐릭터 카카오톡 이모티콘 6종 세트. 표현된 감정은 다음과 같아야 합니다: 1. 큰 소리로 웃음, 2. 큰 눈물을 흘리며 울음, 3. 눈에 불을 켜고 화냄, 4. 하트 보내기, 5. 입을 크게 벌리고 충격받음, 6. 평화롭게 잠듦. 단순하고 굵은 윤곽선, 스티커 스타일, 투명 배경.

### 3. 창작 & 라이프스타일

#### 3.1. 운동 자세 교정, 헬스 & 필라테스 장면
*   **상황**: 유튜브나 블로그에 올릴 운동 콘텐츠의 자세 시범 이미지가 필요하거나, 개인적으로 정확한 자세를 확인하고 싶을 때
*   **팁**: `anatomically correct`, `muscle definition` 키워드로 정확성을 높이고, 운동 기구와 자세를 구체적으로 묘사하세요.
*   **프롬프트 예시**:
    > Anatomically correct illustration of a woman performing a perfect 'deadlift' exercise in a modern gym. Show clear muscle definition in the legs, back, and arms. The style should be a clean, instructional diagram, highlighting the correct posture and form. Side view.

#### 3.2. 여행 계획을 한눈에, 여행 일정표 시각화
*   **상황**: 복잡한 텍스트 기반의 여행 계획을 친구나 가족과 공유하기 위해 보기 좋은 인포그래픽 스타일의 일정표로 만들고 싶을 때
*   **팁**: `travel itinerary infographic`, `timeline`, `map with icons` 키워드를 사용하고, 날짜별 장소와 활동을 요약하여 제시하세요.
*   **프롬프트 예시**:
    > Travel itinerary infographic for a 3-day trip to Jeju Island, South Korea. Day 1: Airport, Coastal Drive, Hyeopjae Beach. Day 2: Hallasan Mountain hiking, Seogwipo Market. Day 3: Seongsan Ilchulbong, Udo Island, Airport. Use a timeline format with a simple map and cute icons for each location and activity. Bright and cheerful color palette.

#### 3.3. 나만의 요리책 만들기, 레시피 카드
*   **상황**: 나만의 특별한 레시피를 블로그에 올리거나 친구에게 선물하기 위해 예쁜 레시피 카드로 디자인하고 싶을 때
*   **팁**: `recipe card design`, `ingredients list`, `step-by-step instructions` 키워드를 사용하고, 완성된 요리 사진을 포함하도록 요청하세요.
*   **프롬프트 예시**:
    > Recipe card design for 'Kimchi Fried Rice'. The card should feature a delicious-looking, top-down photo of the finished dish in a bowl. On the side, include a section for 'Ingredients' with small icons (e.g., rice, kimchi, egg) and a section for 'Instructions' with numbered steps. The style should be rustic and cozy.

#### 3.5. 기출문제 시각화로 시험 완벽 대비
*   **상황**: 어려운 기출문제(예: 수능, 자격증 시험)의 핵심 개념이나 풀이 과정을 도식화하여 쉽게 암기하고 싶을 때
*   **팁**: `mind map`, `visual summary` 키워드를 사용하고, 문제의 핵심 개념과 관계를 명확히 설명해주세요.
*   **프롬프트 예시**:
    > 해당 기출문제에 대해서 상세한 풀이와 정답을 적어줘, 풀이는 파란색 펜 색으로 적어줘

#### 3.10. 여성 프로필 사진 (스튜디오 촬영 버전)
*   **프롬프트 예시**:
    > A high-key beauty portrait,with porcelain skin and subtle pink-toned makeup, featuring soft peachy blush and glossy lips. Her dark hair is neatly tied back with a few loose strands framing her face, she touch her cheek gently like a professional beauty model, enhancing her serene expression. The image is shot at eye level with a shallow depth of field, capturing the glow of her skin under diffused natural light against a pure white background, evoking a clean, soft, and ethereal aesthetic.

---

## Part 1. 이미지 생성: 세상에 없던 비주얼의 탄생

### 📷 사실적인 사진 스타일

#### 초급: 중립 조명 인물 사진 (성공률 98%)
깔끔하고 기본적인 인물 사진 생성에 최적화됨.
*   **프롬프트 예시**:
    > Portrait of a young Korean woman, neutral lighting, grey background, high resolution photography, 85mm lens.

#### 중급: 풍경 사진
자연, 도시 등 배경 중심의 고해상도 이미지.
*   **프롬프트 예시**:
    > Breathtaking landscape of Hallasan mountain in spring, blooming azaleas, morning mist, golden sunlight, wide angle shot, 8k resolution.

#### 고급: 시네마틱 인물 사진 (성공률 92%)
영화 같은 조명과 분위기 연출.
*   **프롬프트 예시**:
    > Cinematic portrait of an old fisherman, weathered face, rain falling, dramatic lighting, neon lights reflecting on wet pavement in the background, cyberpunk atmosphere, highly detailed.

### 🎨 일러스트 & 스티커

#### 카와이 스타일 스티커
귀여운 캐릭터, 다이어리 꾸미기용.
*   **프롬프트 예시**:
    > Cute sticker of a white fluffy dog eating a watermelon, kawaii style, thick white outline, pastel colors, vector art.

#### 미니멀 스타일
단순하고 깔끔한 선과 색상.
*   **프롬프트 예시**:
    > Minimalist line art of a single rose, continuous line drawing, black ink on white paper.

### 🧸 3D 피규어 & 캐릭터

#### 1/7 스케일 피규어 (단계별 가이드)
1.  **1단계**: 원본 캐릭터 일러스트 생성
    > Anime character design of a magical girl with pink hair and a star wand, full body, vibrant colors.
2.  **2단계**: 피규어 제작 (1단계 이미지 업로드 후)
    > Turn this character into a high quality 1/7 scale PVC figurine, glossy finish, plastic texture, white studio background.

#### 치비 니트 인형 (단계별 가이드)
1.  **1단계**: 캐릭터 디자인 생성
    > Cute baby penguin character design, simple shapes.
2.  **2단계**: 니트 인형 제작 (1단계 이미지 업로드 후)
    > Transform this character into a handmade knitted plushie, wool texture, soft lighting, cozy atmosphere.

#### 가챠폰 캡슐 (성공률 85%)
캡슐 안에 들어있는 작은 장난감 스타일.
*   **프롬프트 예시**:
    > Miniature toy of a sushi roll inside a clear plastic gachapon capsule, realistic plastic texture, studio lighting.

#### 플러시 토이
푹신한 봉제 인형 느낌.
*   **프롬프트 예시**:
    > Soft plush toy of a blue monster, furry texture, stitching details, isolated on white background.

### 🏷️ 로고 & 브랜딩

#### 미니멀 로고
심플하고 기억하기 쉬운 로고 심볼.
*   **프롬프트 예시**:
    > Minimalist logo design for a coffee shop named 'Bean', using a coffee bean icon and simple typography, black and white.

#### 표현적 로고 (구글 공식 예시)
브랜드의 특징을 예술적으로 표현한 로고.
*   **프롬프트 예시**:
    > Expressive logo for an art studio, colorful brush strokes forming the letter 'A', creative and artistic style.

---

## Part 2. 이미지 편집: 기존 이미지를 새롭게
*Pro-Tip: 이미지 편집은 '이미지 업로드' 기능을 사용하여 1단계 베이스 이미지 생성 후 2단계 편집을 진행합니다.*

### 🌄 배경 변경 & 합성
*   **1단계: 베이스 이미지 생성**: 배경을 변경할 인물 사진을 생성합니다.
*   **2단계: 배경 변경**: 1단계에서 생성된 이미지를 업로드한 후, 배경 변경 프롬프트를 실행합니다.
    > Change the background to a tropical beach with palm trees and blue ocean.

### ✂️ 요소 추가/제거
*   **요소 제거 워크플로우**
    1.  **1단계**: 편집할 원본 이미지를 생성합니다.
    2.  **2단계**: 1단계 이미지를 업로드한 후, "Remove the person in the background" 등의 프롬프트로 요소를 제거합니다.
*   **요소 추가 워크플로우**
    1.  **1단계**: 요소를 추가할 배경 이미지를 생성합니다.
    2.  **2단계**: 1단계 이미지를 업로드한 후, "Add a red balloon in the sky" 등의 프롬프트로 요소를 추가합니다.

### 🎭 스타일 전환
*   **1단계**: 스타일을 변경할 원본 사진을 생성합니다.
*   **2단계**: 1단계 이미지를 업로드한 후, "Make it into a oil painting" 등의 프롬프트로 스타일을 전환합니다.

### 🎨 색상 복원 & 리마스터링
*   **1단계**: 복원할 흑백 사진을 생성합니다.
*   **2단계**: 1단계 이미지를 업로드한 후, "Colorize this photo" 등의 프롬프트로 색상을 복원합니다.

---

## Part 3. 비즈니스 & 마케팅: 팔리는 콘텐츠의 비밀

### 📦 제품 사진 & 목업
*   **초급: 깔끔한 제품 사진 (성공률 100%)**: 스튜디오 조명의 깔끔한 제품 샷.
    > Professional product photography of a glass perfume bottle, white background, soft studio lighting, reflection.
*   **고급: 하이엔드 상업 제품 렌더링**: 고급스러운 연출 샷.
    > High-end commercial product rendering of a luxury watch, dark moody lighting, placed on a black marble surface, gold accents.

### 📢 광고 이미지
*   **1단계**: 광고에 사용할 배경 이미지를 생성합니다.
    > Bright and airy living room background, blurred, morning sunlight.
*   **2단계**: 1단계 이미지를 업로드한 후, 광고 텍스트를 추가합니다.
    > Add text "Spring Sale" in bold white font in the center.

### 📱 소셜 미디어 콘텐츠
*   **유튜브 썸네일**: 클릭을 부르는 강렬한 텍스트와 이미지 조합.
*   **폴라로이드 스타일 (소셜 트렌드)**: 감성적인 인스타그램용 이미지.

### 💼 상세페이지 이미지 기획 (예시: 꿀고구마)
**기획 의도**: "실패 없는 꿀고구마" (타겟: 3040 주부 및 1인 가구)

*   **Section 1. 인트로 (Hook)**
    *   목표: 3초 안에 시각적 식욕 자극 및 이탈 방지
    *   핵심 비주얼: 갓 구워 김이 모락모락 나고, 노란 속살에 꿀 진액이 흐르는 클로즈업 GIF/영상.
    *   카피: "퍽퍽하고 목메는 고구마는 그만!", "한 입 베어 물면 입안 가득 퍼지는 달콤함"
*   **Section 2. 당도 증명 (Why Us)**
    *   목표: '맛'에 대한 불신 해소
    *   핵심 내용: '큐어링(Curing)' 숙성 기술 강조. 수확 후 O일간의 숙성 과정 도식화, Brix(당도) 측정기 비교.
*   **Section 3. 산지 및 품종 (Origin)**
    *   목표: 품질 신뢰도 확보
    *   핵심 내용: '황토밭'과 '베니하루카' 키워드. 붉은 황토밭 전경과 농부 사진.
*   **Section 4. 선별 및 세척 과정 (Process)**
    *   목표: 썩은 고구마/흙 묻은 고구마에 대한 피로감 해결
    *   핵심 내용: 기계 선별 + 육안 선별 및 세척 공정 GIF. "흙 무게는 뺍니다."
*   **Section 5. 사이즈 가이드 (Detail)**
    *   목표: 정확한 사이즈 제안으로 반품 방지
    *   핵심 내용: 종이컵/휴대폰과 실제 고구마 크기 비교 사진. (한입/중/특대 사이즈 비교)
*   **Section 6. 맛있게 먹는 법 & 보관법 (How to)**
    *   목표: 정보 제공을 통한 체류 시간 증대
    *   핵심 내용: 에어프라이어 레시피 ("180도 30분, 뒤집어서 10분"), 보관 주의사항(추운 곳 금지).
*   **Section 7. 배송 및 AS 정책 (Trust)**
    *   목표: 마지막 구매 망설임 제거
    *   핵심 내용: 안전한 박스 포장 사진, 100% 처리 약속.

---

## Part 4. 교육 & 학습: 복잡한 지식의 시각화

### 📊 인포그래픽
*   **머신러닝 인포그래픽**: 복잡한 알고리즘을 쉽게 설명.
    > Infographic explaining the concept of machine learning, simple vector style, blue and white color scheme.
*   **식물 인포그래픽 (구글 공식 예시)**: 1단계(식물 사진) -> 2단계(인포그래픽 생성) -> 3단계(한국어 번역).
*   **레시피 인포그래픽**: 1단계(요리 과정) -> 2단계(한국어 번역).

### 📐 다이어그램 & 청사진
*   **라이트 형제 비행기 청사진**: 구조와 설계를 보여주는 블루프린트 스타일.
    > Blueprint of the Wright brothers' airplane, white lines on blue background, technical drawing style.
*   **타지마할 청사진**: 건축물의 상세 도면 스타일.

### 📚 학습 자료
*   **태양계 인포그래픽**: 행성 배치와 정보 시각화.
    > Solar system infographic, showing the sun and planets in order, realistic style, dark background with stars.

### 🏗️ 데이터 시각화
*   **1단계**: 건축 도면 생성.
*   **2단계**: 1단계 이미지를 업로드하여 3D 렌더링 생성.

---

## Part 5. 창작 & 엔터테인먼트: 상상력의 무한한 확장

### 📖 만화 & 스토리보드
*   **4컷 만화**: 기승전결이 있는 짧은 만화 생성. (캐릭터 변경 및 한글 번역 가능)
*   **스토리보드 (구글 공식 예시)**:
    1.  **1단계**: 장면 설명 작성 (텍스트) - "한 남자가 어두운 골목길을 걷다가..."
    2.  **2단계**: 스토리보드 생성 - 4컷 패널로 장면 시각화.

### 👤 캐릭터 디자인
*   **기본 템플릿**: 전신/반신, 스타일(애니/실사), 의상, 포즈 등을 지정하여 캐릭터 시트 생성.
    > Character design sheet of a female warrior, fantasy style, wearing silver armor, holding a sword, front view, side view, back view, white background.

### 🧸 플러시 토이 & 굿즈
*   **1단계**: 캐릭터 디자인 생성.
*   **2단계**: 생성된 캐릭터 이미지를 업로드하여 플러시 토이(봉제 인형) 제작.

### 😂 밈 & 패러디
*   유행하는 밈 템플릿에 나만의 캐릭터나 텍스트를 합성하여 패러디 이미지 생성.

---

## Part 6. 고급 활용

### 🔧 실패 수정 가이드
1.  **신원 왜곡 수정**
    *   문제: 얼굴이 일관되지 않거나 왜곡됨.
    *   해결: `"maintain exact facial features"` 추가, 참조 이미지 사용, `"photorealistic portrait"` 명시.
2.  **플라스틱 피부 질감 수정**
    *   문제: 피부가 인형처럼 보임.
    *   해결: `"natural skin texture with pores"`, `"realistic skin imperfections"`, `"professional photography, not CGI"` 추가.
3.  **텍스트 렌더링 수정**
    *   문제: 텍스트가 흐릿하거나 잘못됨.
    *   해결: 정확한 텍스트를 따옴표("")로 명시, 폰트 스타일 구체화(`"bold sans-serif"`), 배경 대비 명시.
4.  **조명 & 그림자 충돌 수정**
    *   문제: 조명이 부자연스럽거나 그림자가 이상함.
    *   해결: 광원 방향 명시(`"from left"`), `"consistent lighting"`, `"natural shadows"` 추가.

### 🎭 다중 이미지 융합
*   **두 캐릭터 융합**: 캐릭터 A 생성 -> 캐릭터 B 생성 -> 두 이미지를 모두 업로드하여 하나의 장면으로 융합.
*   **다중 캐릭터 일관성**: 최대 14개까지 개별 캐릭터 생성 후 하나의 장면에 합성 가능.

### 🎯 전문가 워크플로우 (5단계 개선)
1.  **초기 생성**: 기본 프롬프트로 시작.
2.  **조명 조정**: 조명 설명 구체화.
3.  **디테일 추가**: 질감, 재질 명시.
4.  **구성 개선**: 카메라 각도, 구도 조정.
5.  **최종 다듬기**: 품질 수정자(Quality Modifiers) 추가.

### 💡 마지막 팁
*   **시작 템플릿**: 프로필은 Simple Portrait, 제품은 Commercial Product Rendering.
*   **실패 수정**: 피부 질감, 텍스트, 조명 키워드 기억하기.
*   **똑똑하게 확장하기**: 다단계 개선 방법, 캐릭터 일관성 유지 기법, 배치 처리 활용.

---

## Part 7. 추가 활용 사례
*   **지역 명소 아이소메트릭**: 대구, 이태원 등의 지역 명소를 3D 아이소메트릭 뷰로 시각화하는 예시.

## Part 8. 고정밀 이미지 생성을 위한 JSON 프롬프트 생성 기법
*(12월 초 업데이트 예정)*

---

## 부록: 나노바나나 PRO 프롬프트 작성 공식

### 🚀 나노바나나 PRO란?
*   **나노바나나 PRO (Gemini 3 Pro Image)**는 Google DeepMind가 2025년 11월 20일 공식 발표한 최첨단 이미지 생성 및 편집 모델입니다.
*   **주요 특징**: 향상된 추론, 실시간 정보 반영(날씨/스포츠 등), 다국어 텍스트 렌더링, 다중 이미지 블렌딩(최대 14개), 인물 일관성(최대 5명), 2K/4K 고해상도 지원.

### 🎓 프롬프트 작성의 7가지 황금 법칙
1.  **초-구체적 묘사 (Hyper-specific Description)**: 단순 키워드 나열이 아닌, 사진작가처럼 조명, 앵글, 질감을 구체적으로 묘사하세요.
2.  **캐릭터 일관성 유지 (Character Consistency)**: 캐릭터 시트를 만들거나 이전 이미지를 참조하여 일관성을 유지하세요.
3.  **맥락과 의도 제공 (Context and Intent)**: 이미지가 어디에 쓰일지(웹사이트 배너, 인스타 스토리 등) 명시하세요.
4.  **반복적 개선 (Iterative Refinement)**: 한 번에 완벽하려 하지 말고, 단계를 나눠 디테일을 추가하세요.
5.  **의미론적 부정 프롬프트 (Semantic Negative Prompts)**: 원하지 않는 요소(blur, distortion)를 명확히 배제하세요.
6.  **종횡비 제어 (Aspect Ratio Control)**: `16:9`(유튜브), `9:16`(인스타), `Square` 등 용도에 맞는 비율을 지정하세요.
7.  **카메라 제어 (Camera Control)**: `85mm`(인물), `wide-angle`(풍경), `macro`(접사), `drone shot`(조감도), `bokeh`(아웃포커싱) 등 렌즈 용어를 활용하세요.

### ⚠️ 실패하는 프롬프트 vs 성공하는 프롬프트
*   **조명**: "good lighting" (X) -> "soft diffused north-facing window light, golden hour warmth" (O)
*   **스타일**: "real & illustration" (X) -> "photorealistic style" 또는 "illustrated style" 중 하나만 선택 (O)
*   **텍스트**: "text says SALE" (X) -> "bold red sans-serif text 'SALE' centered on white background" (O)
