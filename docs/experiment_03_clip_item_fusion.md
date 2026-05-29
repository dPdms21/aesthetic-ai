# Experiment 03. CLIP Item-level Feature Fusion

## 1. Purpose

Experiment 03의 목적은 Experiment 02에서 사용한 grid image 기반 착장 조화 분류 방식의 한계를 보완하는 것이다.

Experiment 02에서는 각 outfit을 구성하는 fashion item 이미지를 하나의 3x3 grid image로 합성한 뒤, ResNet18을 이용해 compatible/incompatible을 분류하였다. 이 방식은 outfit 전체를 하나의 이미지처럼 처리할 수 있다는 장점이 있지만, 각 item 간의 관계를 명시적으로 표현하지 못한다는 한계가 있었다.

따라서 Experiment 03에서는 각 fashion item 이미지를 개별적으로 처리한다. 각 item image를 CLIP image encoder에 입력하여 item-level embedding을 추출하고, 이를 outfit-level feature로 결합한 뒤 MLP classifier를 학습하였다.

최종 목표는 착장 조화 판단에서 item-level semantic feature, item 간 relation feature, color harmony feature, category-aware relation feature가 성능 개선에 기여하는지 확인하는 것이다.

---

## 2. Background

착장 조화는 단순한 이미지 미감 분류 문제가 아니다.

일반 이미지 aesthetic classification은 전체 이미지의 구도, 색감, 선명도, 조명 등 이미지 전체의 품질을 평가하는 문제에 가깝다. 반면 outfit compatibility prediction은 여러 fashion item이 하나의 착장으로 조합되었을 때 서로 어울리는지를 판단하는 문제이다.

착장 조화에는 다음 요소들이 함께 작용한다.

- item 자체의 시각적 의미
- item 간 스타일 일관성
- 상의, 하의, 신발, 가방 등 category별 역할
- item 간 색감 조화
- 채도, 명도, 색상 간 거리
- 특정 item의 이질감 또는 과도한 시각적 강조

Experiment 02의 grid image baseline은 이러한 복합적인 관계를 직접 표현하지 못했다. Experiment 03에서는 이를 보완하기 위해 item-level feature fusion 구조를 실험하였다.

---

## 3. Dataset

Experiment 03은 Experiment 02에서 구성한 Polyvore 기반 outfit compatibility dataset을 재사용하였다.

### Source datasets

- `xthan/polyvore-dataset`
  - `fashion_compatibility_prediction.txt`
  - compatibility label과 outfit item key 제공

- `Marqo/polyvore`
  - item image
  - category
  - text
  - item_ID 제공

### Final samples

Experiment 02에서 최종적으로 사용한 fully matched sample은 총 2,420개이다.

| Split | Incompatible | Compatible | Total |
|---|---:|---:|---:|
| Train | 1,025 | 911 | 1,936 |
| Validation | 256 | 228 | 484 |
| Total | 1,281 | 1,139 | 2,420 |

Experiment 03에서는 Experiment 02와 동일한 train/validation split을 유지하였다. 이를 통해 Experiment 02의 ResNet18 grid baseline과 직접 비교할 수 있도록 하였다.

---

## 4. Metadata Reconstruction

Experiment 02에서 생성한 `labels_split.csv`에는 다음 정보가 포함되어 있었다.

- `image_path`
- `label`
- `sample_id`
- `num_items`
- `split`

그러나 CLIP item-level 실험에는 각 outfit을 구성하는 item list가 필요하다. 따라서 Experiment 03에서는 item-level metadata를 재구성하였다.

초기에는 `labels_split.csv`의 `sample_id`를 `fashion_compatibility_prediction.txt`의 원본 line index와 동일하다고 가정했지만, 이 방식은 잘못된 매핑을 만들었다. 실제로 `sample_id`는 원본 compatibility file의 line index가 아니라, Marqo item image와 fully matched된 sample list 기준 index였다.

따라서 다음 절차로 metadata를 재구성하였다.

1. `fashion_compatibility_prediction.txt`에서 label과 item key 목록을 로드한다.
2. `Marqo/polyvore`의 `item_ID`와 compatibility item key를 매칭한다.
3. 모든 item이 Marqo dataset에 존재하는 sample만 유지한다.
4. fully matched sample 2,420개를 재구성한다.
5. `labels_split.csv`의 `sample_id`를 fully matched sample list의 index로 사용한다.
6. 최종 item-level metadata를 저장한다.

최종적으로 다음 파일을 생성하였다.

```text
item_level_samples.json
item_level_samples_summary.csv
```

---

## 5. Method

Experiment 03에서는 CLIP ViT-B/32 image encoder를 사용하였다.

각 outfit은 여러 item image로 구성된다. 각 item image를 CLIP image encoder에 입력하여 512차원 embedding을 추출하였다. 이후 다양한 방식으로 item embedding을 outfit-level feature로 결합하였다.

### 5.1 CLIP mean pooling

각 outfit의 item embedding을 평균내어 512차원 outfit feature를 생성하였다.

```text
item embeddings: (num_items, 512)
mean pooling: (512,)
```

이 방식은 outfit의 전체적인 semantic 분위기를 표현할 수 있지만, item 간 관계를 직접 반영하지 못한다.

### 5.2 CLIP mean + max pooling

Mean pooling feature와 max pooling feature를 연결하여 1024차원 feature를 생성하였다.

```text
mean feature: 512
max feature: 512
combined feature: 1024
```

이 방식은 특정 item에서 강하게 나타나는 feature를 보존하기 위한 시도였다.

### 5.3 Tuned MLP

CLIP mean pooling feature를 유지한 상태에서 MLP classifier의 regularization을 강화하였다.

변경한 설정은 다음과 같다.

- hidden dimension 감소
- dropout 증가
- weight decay 증가
- early stopping 적용

이는 과적합을 줄이고 validation 성능을 안정화하기 위한 실험이었다.

### 5.4 Pairwise relation stats

Mean pooling만으로는 item 간 관계를 표현하기 어렵기 때문에, outfit 내부 item embedding 간 cosine similarity를 계산하였다.

각 outfit에 대해 다음 6개의 relation stats를 생성하였다.

- pairwise mean similarity
- pairwise min similarity
- pairwise max similarity
- pairwise std similarity
- pairwise range similarity
- scaled number of items

최종 feature는 다음과 같다.

```text
CLIP mean embedding: 512
pairwise relation stats: 6
combined feature: 518
```

### 5.5 Color harmony stats

착장 조화에서 색감은 중요한 요소이므로, item image에서 RGB/HSV 기반 color harmony stats를 추출하였다.

각 item image에서 평균 RGB와 HSV 값을 계산하고, outfit 단위로 다음 10개의 color stats를 생성하였다.

- RGB pairwise mean distance
- RGB pairwise min distance
- RGB pairwise max distance
- RGB pairwise std distance
- mean hue
- mean saturation
- mean value
- std hue
- std saturation
- std value

최종 feature는 다음과 같다.

```text
CLIP mean embedding: 512
pairwise relation stats: 6
color harmony stats: 10
combined feature: 528
```

Color stats는 feature scale 차이를 줄이기 위해 feature-wise standardization을 적용하였다.

### 5.6 Category-aware relation stats

기존 pairwise relation stats는 outfit 내부의 모든 item pair를 동일하게 취급한다. 그러나 실제 착장 조화에서는 category별 관계가 서로 다른 의미를 가진다.

예를 들어 상의-하의, 하의-신발, 상의-신발 관계는 전체 스타일 통일감에 직접적인 영향을 줄 수 있고, 가방이나 액세서리는 전체 outfit과의 거리감 또는 포인트 요소로 작용할 수 있다.

따라서 Marqo category를 rough category group으로 매핑하였다.

```text
top / bottom / shoes / bag / accessory / outer / dress / clothing / other
```

이후 주요 category pair별 CLIP embedding similarity 통계를 계산하였다.

사용한 category pair는 다음과 같다.

- main-shoes
- accessory-main
- bag-main
- outer-main
- top-shoes
- bottom-shoes
- top-bottom
- dress-shoes

각 category pair마다 다음 5개 feature를 생성하였다.

- mean similarity
- min similarity
- max similarity
- std similarity
- availability flag

최종 category-aware relation stats는 다음과 같다.

```text
8 category pairs × 5 stats = 40 dimensions
```

기존 Step 14 feature에 category-aware relation stats를 추가한 최종 feature 구성은 다음과 같다.

```text
CLIP mean embedding: 512
pairwise relation stats: 6
color harmony stats: 10
category-aware relation stats: 40
combined feature: 568
```

Category-aware relation stats는 feature scale 차이를 줄이기 위해 feature-wise standardization을 적용하였다.

---

## 6. Classifier

각 feature는 MLP classifier에 입력하였다.

기본 classifier 구조는 다음과 같다.

```text
Linear(input_dim → 256)
ReLU
Dropout(0.3)
Linear(256 → 2)
```

Loss function과 optimizer는 다음과 같다.

- Loss: CrossEntropyLoss
- Optimizer: Adam
- Learning rate: 1e-3
- Weight decay: 1e-4
- Batch size: 32
- Epochs: 40

최종 모델은 동일한 학습 설정에서 seed 반복 실험을 수행하여 결과 안정성을 확인하였다.

---

## 7. Results

### 7.1 Overall results

| Experiment | Feature | Input dim | Best validation accuracy | Interpretation |
|---|---|---:|---:|---|
| Experiment 02 baseline | ResNet18 grid image | - | 0.6818 | Grid image 기반 착장 조화 baseline |
| Experiment 03 - Step 6 | CLIP mean pooling + MLP | 512 | 0.6777 | 단순 mean pooling은 grid baseline을 넘지 못함 |
| Experiment 03 - Step 8 | CLIP mean + max pooling + MLP | 1024 | 0.6570 | Feature 차원 증가 후 성능 하락 |
| Experiment 03 - Step 9 | CLIP mean pooling + tuned MLP | 512 | 0.6157 | 강한 regularization으로 성능 하락 |
| Experiment 03 - Step 11 | CLIP mean pooling + pairwise relation stats + MLP | 518 | 0.7128 | Item 간 관계 정보 추가로 baseline 개선 |
| Experiment 03 - Step 14 | CLIP mean pooling + pairwise relation stats + color stats + MLP | 528 | 0.7727 | 관계 정보와 색감 정보를 함께 반영하여 성능 개선 |
| Experiment 03 - Step 19 | CLIP mean pooling + pairwise relation stats + color stats + category-aware relation stats + MLP | 568 | 0.8285 | Category별 item 관계를 반영하여 최종 최고 성능 달성 |

### 7.2 Final model result

Experiment 03의 최종 대표 모델은 다음과 같다.

```text
CLIP ViT-B/32 mean pooling
+ pairwise item relation stats
+ color harmony stats
+ category-aware relation stats
+ MLP classifier
```

최종 단일 실행 성능은 다음과 같다.

| Metric | Value |
|---|---:|
| Best validation accuracy | 0.8285 |
| Macro-F1 | 0.8271 |
| Weighted-F1 | 0.8280 |
| Input dimension | 568 |
| Baseline accuracy | 0.6818 |
| Improvement over baseline | +0.1467 |

Experiment 02의 ResNet18 grid baseline 대비 약 14.7%p 성능이 향상되었다.

### 7.3 Final confusion matrix

최종 모델의 validation confusion matrix는 다음과 같다.

```text
[[222, 34],
 [ 49,179]]
```

Class-wise 성능은 다음과 같다.

| Class | Precision | Recall | F1-score | Support |
|---|---:|---:|---:|---:|
| Incompatible | 0.8192 | 0.8672 | 0.8425 | 256 |
| Compatible | 0.8404 | 0.7851 | 0.8118 | 228 |
| Macro avg | 0.8298 | 0.8261 | 0.8271 | 484 |
| Weighted avg | 0.8292 | 0.8285 | 0.8280 | 484 |

### 7.4 Seed stability check

최종 모델의 결과가 단일 실행의 우연인지 확인하기 위해 seed 3개로 반복 실험을 수행하였다.

| Seed | Best epoch | Best validation accuracy | Macro-F1 | Validation loss |
|---:|---:|---:|---:|---:|
| 42 | 28 | 0.8264 | 0.8261 | 0.4165 |
| 123 | 27 | 0.8244 | 0.8226 | 0.4139 |
| 2026 | 32 | 0.8285 | 0.8281 | 0.4047 |

Seed 반복 결과 요약은 다음과 같다.

| Metric | Value |
|---|---:|
| Mean best validation accuracy | 0.8264 |
| Min best validation accuracy | 0.8244 |
| Max best validation accuracy | 0.8285 |
| Accuracy range | 0.0041 |
| Mean Macro-F1 | 0.8256 |

세 seed의 validation accuracy가 모두 0.824 이상으로 나타났고, seed 간 성능 차이가 매우 작았다. 따라서 최종 모델의 성능 개선은 단일 실행의 우연한 결과가 아니라, feature 구조 자체가 안정적으로 효과를 가진다고 해석할 수 있다.

---

## 8. Analysis

### 8.1 CLIP mean pooling의 한계

CLIP mean pooling은 item-level semantic feature를 outfit 단위로 결합하는 가장 단순한 방식이다. 그러나 validation accuracy는 0.6777로, Experiment 02의 grid baseline 0.6818을 넘지 못했다.

이는 CLIP item embedding 자체는 outfit compatibility 판단에 유용한 정보를 포함하지만, 단순 평균만으로는 item 간 관계를 충분히 표현하기 어렵다는 것을 보여준다.

### 8.2 Mean + max pooling의 성능 하락

Mean + max pooling은 feature dimension을 1024로 증가시켰지만 validation accuracy는 0.6570으로 하락하였다.

이는 현재 데이터 규모에서 feature dimension 증가가 과적합 위험을 높였거나, max pooling이 특정 item의 강한 특징을 과도하게 반영하여 전체 compatibility 판단을 흐렸을 가능성을 보여준다.

### 8.3 강한 regularization의 실패

Tuned MLP는 dropout과 weight decay를 강화했지만 validation accuracy가 0.6157로 하락하였다.

이는 regularization이 과하게 적용되어 모델이 충분히 학습하지 못했을 가능성을 시사한다.

### 8.4 Pairwise relation feature의 효과

Pairwise relation stats를 추가했을 때 validation accuracy는 0.7128로 상승하였다.

이는 착장 조화 판단에서 item 간 관계 정보가 중요함을 보여준다. 특히 item embedding 간 cosine similarity 통계는 outfit 내부 item들이 의미적으로 얼마나 유사하거나 이질적인지를 표현한다.

### 8.5 Color harmony feature의 효과

Color harmony stats를 추가했을 때 validation accuracy는 0.7727로 크게 향상되었다.

이는 착장 조화 판단에서 색감 정보가 중요한 역할을 한다는 것을 보여준다. RGB 색상 거리와 HSV 기반 채도, 명도, 색상 분산 정보는 CLIP embedding과 pairwise relation stats가 직접적으로 표현하지 못하는 색감 조화 요소를 보완한 것으로 해석할 수 있다.

### 8.6 Category-aware relation feature의 효과

Category-aware relation stats를 추가했을 때 validation accuracy는 0.8285로 상승하였다.

기존 pairwise relation stats는 모든 item pair를 동일하게 취급하였다. 반면 category-aware relation stats는 main-shoes, bag-main, accessory-main, top-bottom, top-shoes, bottom-shoes 등 착장 내 주요 category 관계를 분리하여 반영한다.

이 결과는 착장 조화 판단에서 단순한 item 간 평균 관계뿐 아니라, 어떤 category끼리의 관계인지가 중요하다는 점을 보여준다. 특히 신발과 메인 의류, 가방과 메인 의류, 액세서리와 메인 의류의 관계는 스타일 통일감과 포인트 요소를 판단하는 데 중요한 역할을 할 수 있다.

---

## 9. Final Model

Experiment 03의 최종 대표 모델은 다음 구조로 설정한다.

```text
Item image
→ CLIP ViT-B/32 image encoder
→ Item embeddings
→ CLIP mean embedding
→ Pairwise item relation stats
→ Color harmony stats
→ Category-aware relation stats
→ MLP classifier
→ Compatible / Incompatible prediction
```

최종 모델 feature 구성은 다음과 같다.

| Feature group | Dimension | Description |
|---|---:|---|
| CLIP mean embedding | 512 | Outfit의 item-level semantic 평균 표현 |
| Pairwise relation stats | 6 | 전체 item embedding 간 cosine similarity 기반 관계 통계 |
| Color harmony stats | 10 | RGB/HSV 기반 색감 조화 통계 |
| Category-aware relation stats | 40 | 주요 category pair별 item relation 통계 |
| Total | 568 | 최종 MLP 입력 feature |

최종 대표 성능은 다음과 같다.

```text
Best validation accuracy: 0.8285
Seed-averaged validation accuracy: 0.8264
Macro-F1: 0.8271
```

---

## 10. Conclusion

Experiment 03에서는 CLIP 기반 item-level feature fusion을 통해 Polyvore outfit compatibility classification 성능을 개선하였다.

단순 CLIP mean pooling은 grid image baseline과 유사한 수준에 머물렀지만, item 간 pairwise relation stats를 추가하자 validation accuracy가 0.7128로 향상되었다. 이후 RGB/HSV 기반 color harmony stats를 추가했을 때 validation accuracy는 0.7727까지 상승하였다. 마지막으로 category-aware relation stats를 추가했을 때 validation accuracy는 0.8285까지 향상되었다.

이 결과는 착장 조화 판단에서 다음 네 가지 요소가 함께 중요하다는 점을 보여준다.

1. Item-level semantic feature
2. Item-to-item relation feature
3. Color harmony feature
4. Category-aware item relation feature

따라서 착장 미감 평가 AI는 단일 이미지 feature만 사용하는 구조보다, item 단위 의미 정보와 관계 정보, 색감 정보, category별 관계 정보를 함께 반영하는 구조가 더 적합하다.

---

## 11. Limitations

현재 실험에는 다음 한계가 있다.

1. Color feature는 평균 RGB/HSV 통계를 기반으로 하므로, 실제 착장에서의 item 면적 비중을 정교하게 반영하지 못한다.
2. Item image의 배경 제거가 완벽하지 않기 때문에 흰 배경이나 이미지 구성 방식이 색감 feature에 영향을 줄 수 있다.
3. 소재, 재질, 패턴 복잡도는 별도의 feature로 명시적으로 반영하지 않았다.
4. Category group mapping은 rule-based 방식이므로, 일부 category가 실제 fashion role과 다르게 매핑될 수 있다.
5. Polyvore compatibility label은 실제 사용자 미감 점수라기보다 outfit compatibility 기반 label이다.
6. 현재 모델은 compatible/incompatible 분류에 집중하며, 사용자에게 직접 제공할 설명 문장을 생성하지는 않는다.

---

## 12. Next Step

Experiment 03에서는 착장 조화 분류 성능 개선 가능성을 확인하였다.

다음 Experiment 04에서는 최종 모델의 예측 결과를 사용자가 이해할 수 있는 피드백으로 변환하는 설명 가능한 구조를 설계한다.

주요 방향은 다음과 같다.

- Color harmony score 해석
- Item 간 relation score 기반 mismatch item 탐지
- Category-aware relation 기반 스타일 통일감 해석
- Compatible/incompatible 예측 결과에 대한 사용자 친화적 피드백 문장 생성
- 색감, 스타일 통일감, item 조화도 관점의 explanation template 설계
- 최종 착장 미감 점수 산출 구조 설계