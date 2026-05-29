# Experiment 04: 설명 가능한 착장 미감 피드백 구조 설계

## 1. 목적

Experiment 04는 Experiment 03에서 만든 최종 feature와 예측 결과를 바탕으로, 사용자가 이해할 수 있는 착장 미감 피드백 구조를 설계하는 단계이다.

이번 실험은 새로운 모델을 학습하거나 성능을 높이는 것이 목적이 아니다.  
compatible / incompatible 예측 결과를 전체 점수와 하위 점수로 변환하고, 각 점수에 맞는 설명 문장을 생성하는 것을 목표로 한다.

---

## 2. 배경

Experiment 03에서는 CLIP item-level feature에 다음 feature들을 함께 사용했을 때 가장 좋은 성능을 얻었다.

- item 간 pairwise relation stats
- color harmony stats
- category-aware relation stats

최종 모델은 단순히 착장이 어울리는지 여부를 예측하는 데 그치지 않고, 각 feature 그룹을 활용해 왜 조화롭거나 어색한지 설명할 수 있는 가능성을 보여준다.

따라서 Experiment 04에서는 이 feature들을 기반으로 설명 가능한 피드백 구조를 만든다.

---

## 3. 피드백 출력 구조

최종 피드백은 다음과 같은 형태로 구성한다.

```json
{
  "overall_score": 82,
  "color_harmony_score": 78,
  "item_relation_score": 84,
  "style_consistency_score": 86,
  "prediction": "compatible",
  "confidence": 0.83,
  "summary_feedback": "전체적으로 아이템 간 조화가 좋은 착장입니다.",
  "color_feedback": "색감은 비교적 안정적이며, 전체 톤이 크게 충돌하지 않습니다.",
  "item_relation_feedback": "아이템 간 시각적 관계가 자연스럽고 조합이 잘 맞습니다.",
  "style_feedback": "상의, 하의, 신발 등 주요 카테고리 간 스타일 통일감이 좋은 편입니다."
}
```

---

## 4. 점수 구성

| 점수 | 의미 |
|---|---|
| `overall_score` | 모델의 compatible 예측 확률을 변환한 전체 착장 점수 |
| `color_harmony_score` | 색감 조화 정도를 나타내는 점수 |
| `item_relation_score` | 아이템 간 전체 조화도를 나타내는 점수 |
| `style_consistency_score` | 주요 카테고리 간 스타일 통일감을 나타내는 점수 |

---

## 5. 점수별 설명 방향

### 5.1 전체 점수

`overall_score`는 모델이 예측한 compatible 확률을 0~100점으로 변환한다.

```text
overall_score = compatible_probability * 100
```

점수가 높을수록 전체 착장이 조화롭다고 해석한다.

### 5.2 색감 조화 점수

`color_harmony_score`는 RGB/HSV 기반 color harmony stats를 사용한다.

이 점수는 착장의 색 조합이 안정적인지, 특정 색이 튀거나 충돌하는지를 설명하는 데 사용한다.

### 5.3 아이템 관계 점수

`item_relation_score`는 item embedding 간 pairwise relation stats를 사용한다.

이 점수는 상의, 하의, 신발, 가방 등 전체 아이템이 하나의 착장으로 자연스럽게 연결되는지를 설명하는 데 사용한다.

### 5.4 스타일 통일감 점수

`style_consistency_score`는 category-aware relation stats를 사용한다.

이 점수는 top-bottom, main-shoes, bag-main 같은 주요 아이템 조합이 스타일적으로 잘 맞는지를 설명하는 데 사용한다.

---

## 6. 피드백 문장 규칙

점수 구간에 따라 간단한 rule-based 문장을 생성한다.

| 점수 구간 | 설명 방향 |
|---|---|
| 80~100 | 매우 조화로운 착장 |
| 60~79 | 전반적으로 무난하고 안정적인 착장 |
| 40~59 | 일부 아이템이나 색감에서 어색함이 있는 착장 |
| 0~39 | 전체적인 조화가 부족한 착장 |

예시:

```text
overall_score가 80 이상이면:
"전체적으로 아이템 간 조화가 좋은 착장입니다."

color_harmony_score가 40 미만이면:
"색 조합에서 다소 충돌이 느껴질 수 있습니다."

style_consistency_score가 낮으면:
"일부 아이템의 스타일 방향이 서로 다르게 느껴질 수 있습니다."
```

---

## 7. 진행 방향

Experiment 04는 다음 순서로 진행한다.

1. 피드백 출력 구조 정의
2. compatible 확률을 overall_score로 변환
3. color harmony score 계산 규칙 설계
4. item relation score 계산 규칙 설계
5. style consistency score 계산 규칙 설계
6. rule-based 피드백 문장 생성
7. validation sample 일부에 대해 피드백 출력 테스트
8. 결과를 문서와 json 파일로 정리

---

## 8. 예상 결과 파일

```text
docs/experiment_04_explainable_feedback.md
src/evaluation/feedback_generator.py
results/experiment_04_feedback_samples.json
```

필요하다면 테스트용 노트북도 추가할 수 있다.

```text
notebooks/experiment_04_explainable_feedback.ipynb
```

---

## 9. 정리

Experiment 04는 모델의 예측 결과를 사용자 친화적인 피드백으로 변환하는 단계이다.

이를 통해 착장 평가 결과를 단순한 compatible / incompatible 분류가 아니라, 전체 점수, 색감 조화, 아이템 관계, 스타일 통일감으로 나누어 설명할 수 있다.

---

## 10. 샘플 출력 테스트

피드백 생성 로직이 정상적으로 동작하는지 확인하기 위해 테스트용 sample 5개를 생성하고, 각 sample에 대해 전체 점수, 하위 점수, 예측 결과, 피드백 문장을 출력하였다.

이번 단계에서는 실제 validation feature를 사용하지 않고, 피드백 출력 구조를 검증하기 위한 임시 입력값을 사용하였다.

생성된 결과 파일은 다음과 같다.

```text
results/experiment_04_feedback_samples.json
```

출력 결과에는 다음 정보가 포함된다.

| 항목 | 설명 |
|---|---|
| `sample_id` | 테스트 sample 식별자 |
| `overall_score` | compatible 확률을 0~100점으로 변환한 전체 점수 |
| `color_harmony_score` | 색감 조화 점수 |
| `item_relation_score` | 아이템 간 조화도 점수 |
| `style_consistency_score` | 스타일 통일감 점수 |
| `prediction` | compatible / incompatible 예측 결과 |
| `confidence` | 예측 class에 대한 confidence |
| `summary_feedback` | 전체 착장 요약 피드백 |
| `color_feedback` | 색감 조화 피드백 |
| `item_relation_feedback` | 아이템 관계 피드백 |
| `style_feedback` | 스타일 통일감 피드백 |

테스트 결과, sample별 점수 구간에 따라 서로 다른 rule-based 피드백 문장이 정상적으로 생성되었다.

높은 점수를 가진 sample은 전체 조화와 스타일 통일감이 좋다는 피드백을 생성했고, 낮은 점수를 가진 sample은 색 조합 충돌, 아이템 간 조화 부족, 스타일 방향의 불명확성을 설명하는 피드백을 생성하였다.

이를 통해 Experiment 04의 기본 피드백 출력 구조가 정상적으로 동작함을 확인하였다.

---

## 11. Feature 기반 하위 점수 계산 및 보정

초기 샘플 출력 테스트에서는 `color_harmony_score`, `item_relation_score`, `style_consistency_score`를 직접 입력하여 피드백 구조가 정상적으로 동작하는지 확인하였다.

이후 Experiment 03에서 사용한 feature group 구조를 반영하여, 각 하위 점수를 feature dict 기반으로 계산하도록 수정하였다.

사용한 feature group은 다음과 같다.

| 하위 점수 | 사용 feature group |
|---|---|
| `color_harmony_score` | RGB/HSV 기반 color harmony stats |
| `item_relation_score` | item embedding 간 pairwise relation stats |
| `style_consistency_score` | category-aware relation stats |

### 11.1 Color Harmony Score

`color_harmony_score`는 RGB 평균 거리, RGB 거리 표준편차, hue/saturation/value 표준편차를 기반으로 계산하였다.

초기 계산식은 감점이 다소 강해 색감이 좋은 sample도 80점 이상으로 잘 올라가지 않는 문제가 있었다.

따라서 RGB/HSV 관련 감점 가중치를 완화하여, 색감 조화 수준이 더 자연스럽게 점수 구간에 반영되도록 보정하였다.

보정 후 color score는 다음과 같이 변화하였다.

| sample_id | 보정 전 | 보정 후 |
|---|---:|---:|
| 0 | 67 | 77 |
| 1 | 54 | 68 |
| 2 | 26 | 48 |
| 3 | 3 | 32 |
| 4 | 78 | 85 |

보정 후에는 좋은 색감 sample은 80점 이상, 중간 수준의 sample은 60~79점, 어색한 색감 sample은 40~59점, 색 충돌이 큰 sample은 0~39점 구간에 더 자연스럽게 배치되었다.

### 11.2 Item Relation Score

`item_relation_score`는 item embedding 간 평균 유사도, 최소 유사도, 유사도 표준편차, 유사도 range, item 수 정보를 기반으로 계산하였다.

평균 유사도와 최소 유사도가 높을수록 아이템 간 관계가 자연스럽다고 보고, 유사도 편차와 range가 클수록 일부 아이템이 전체 착장과 분리될 가능성이 있다고 보아 감점하였다.

### 11.3 Style Consistency Score

`style_consistency_score`는 category-aware relation stats를 기반으로 계산하였다.

주요 category pair는 다음과 같다.

```text
top-bottom
main-shoes
bottom-shoes
top-shoes
bag-main
outer-main
accessory-main
dress-shoes
```

이 중 `top-bottom`, `main-shoes`, `bottom-shoes`처럼 착장의 인상에 큰 영향을 주는 조합에는 더 높은 가중치를 두었다.

이를 통해 단순 평균 유사도가 아니라, 착장 구성에서 중요한 item category 간 스타일 통일감을 더 크게 반영할 수 있도록 하였다.

### 11.4 확인 결과

보정 후 샘플 출력에서는 compatible 확률이 높은 sample이 높은 overall score와 하위 점수를 가지며, 낮은 sample은 색감 조화, 아이템 관계, 스타일 통일감 중 일부에서 낮은 점수를 보였다.

이를 통해 Experiment 03의 feature group을 Experiment 04의 설명 가능한 하위 점수 구조로 변환할 수 있음을 확인하였다.