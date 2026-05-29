# Aesthetic AI

> 착장 사진의 시각적 조화와 미적 완성도를 평가하고, 설명 가능한 피드백 구조로 확장하기 위한 AI 연구 프로젝트

## Project Goal

본 프로젝트는 이미지를 입력으로 받아 시각적 미감과 조화도를 평가하는 AI 모델을 실험하고, 사용자가 이해할 수 있는 피드백을 제공하는 설명 가능한 미감 평가 AI로 확장하는 것을 목표로 한다.

초기 연구 대상은 일반 이미지 전체가 아니라 **착장 사진의 미적 평가**이다.  
특히 코디의 시각적 완성도, item 간 조화, 색감 조화, 스타일 통일감 등을 평가하는 방향으로 실험을 진행한다.

향후에는 장소 기반 코디 추천, UI/PPT/인테리어 피드백 등 다양한 시각 결과물 평가 영역으로 확장할 수 있다.

---

## Main Scope

- AVA 기반 일반 이미지 미감 high/low 분류 baseline
- Polyvore 기반 outfit compatibility classification baseline
- CLIP image encoder 기반 item-level feature fusion
- Item 간 pairwise relation feature 설계
- RGB/HSV 기반 color harmony feature 설계
- Category-aware relation feature 설계
- 설명 가능한 착장 미감 피드백 구조 설계

---

## Current Experiments

| Experiment | Description | Best Validation Accuracy |
|---|---|---:|
| Experiment 01 | AVA 기반 일반 이미지 미감 high/low 분류 baseline | 0.885 |
| Experiment 02 | Polyvore 기반 ResNet18 grid outfit compatibility baseline | 0.6818 |
| Experiment 03 | CLIP item-level fusion + pairwise relation + color stats + category-aware relation | 0.8285 |

---

## Experiment Summary

### Experiment 01

AVA 데이터셋을 이용해 일반 이미지의 미감 high/low 분류 baseline을 구현하였다.  
ResNet18 full fine-tuning 결과 validation accuracy 0.885를 기록하였다.

### Experiment 02

Polyvore 기반 outfit compatibility dataset을 구성하고, 각 outfit item을 3x3 grid image로 합성하여 ResNet18 baseline을 학습하였다.  
최종 validation accuracy는 0.6818이었다.

### Experiment 03

Experiment 02의 grid image 방식이 item 간 관계를 명시적으로 표현하지 못한다는 한계를 보완하기 위해 CLIP 기반 item-level feature fusion을 실험하였다.

최종적으로 다음 feature를 결합했을 때 가장 좋은 성능을 얻었다.

- CLIP mean embedding
- Pairwise item relation stats
- RGB/HSV 기반 color harmony stats
- Category-aware relation stats

최종 validation accuracy는 0.8285로, Experiment 02 baseline 대비 약 14.7%p 개선되었다.  
또한 seed 3회 반복 실험에서 평균 best validation accuracy 0.8264를 기록하여, 최종 feature 구조가 안정적으로 성능 개선에 기여함을 확인하였다.

---

## Repository Structure

```text
aesthetic-ai/
├── docs/
│   └── experiment_03_clip_item_fusion.md
├── notebooks/
│   ├── experiment_01_baseline.ipynb
│   ├── experiment_02_outfit_compatibility_baseline.ipynb
│   └── experiment_03_clip_item_fusion.ipynb
├── src/
│   ├── data/
│   ├── models/
│   ├── training/
│   ├── evaluation/
│   └── utils/
├── results/
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Next Step

다음 단계에서는 Experiment 03의 최종 모델 결과를 바탕으로, 사용자가 이해할 수 있는 설명 가능한 피드백 구조를 설계한다.

주요 방향은 다음과 같다.

- 색감 조화 점수 해석
- item 간 relation score 기반 mismatch item 탐지
- category-aware relation 기반 스타일 통일감 해석
- compatible/incompatible 예측 결과에 대한 피드백 문장 생성
- 색감, 스타일 통일감, item 조화도 관점의 explanation template 설계