# Experiment 02: Outfit Compatibility Classification Baseline

## 1. 실험 목적

Experiment 02는 패션 아이템 조합 데이터를 이용해 착장 조화 여부를 분류할 수 있는지 확인하기 위한 baseline 실험이다.

이번 실험에서는 Polyvore 기반 데이터를 사용하여 다음과 같은 이진 분류 문제를 정의하였다.

```text
0: incompatible outfit
1: compatible outfit
```

이 실험의 목적은 최종 성능 최적화가 아니라, 착장 조화 평가 문제를 실제 데이터셋과 모델 구조로 구성할 수 있는지 확인하는 것이다.

---

## 2. 데이터셋 구성

이번 실험에서는 두 개의 Polyvore 관련 데이터셋을 함께 사용하였다.

```text
xthan Polyvore Dataset
→ outfit compatibility label 및 item key 확보

Marqo Polyvore Dataset
→ item_ID 기준 item image 확보
```

xthan dataset에는 compatibility label과 outfit을 구성하는 item key가 포함되어 있었다.  
하지만 xthan JSON에 포함된 image URL은 실제 이미지가 아니라 HTML 응답을 반환했기 때문에 직접 사용할 수 없었다.

따라서 xthan dataset은 라벨과 item key를 얻는 용도로 사용하고, 실제 item 이미지는 Marqo Polyvore dataset에서 가져왔다.

---

## 3. 데이터 매칭 결과

xthan compatibility file의 item key와 Marqo dataset의 item_ID를 기준으로 이미지를 매칭하였다.

```text
Marqo item count: 94,096
xthan unique item keys: 18,604
matched item keys: 15,285
item-level match ratio: 82.16%
```

전체 compatibility sample은 7,076개였고, 이 중 모든 item image가 매칭된 sample만 최종 사용하였다.

```text
total compatibility samples: 7,076
fully matched valid samples: 2,420
invalid samples: 4,656
valid sample ratio: 34.20%
```

최종 실험에는 이미지까지 확보 가능한 2,420개의 outfit sample을 사용하였다.

---

## 4. 최종 데이터셋

최종 데이터셋의 라벨 분포는 다음과 같다.

```text
label 0 incompatible: 1,281
label 1 compatible: 1,139
```

비율은 다음과 같다.

```text
label 0: 52.93%
label 1: 47.07%
```

두 클래스의 비율이 크게 치우치지 않았기 때문에 이진 분류 baseline 실험에 사용할 수 있다고 판단하였다.

---

## 5. 입력 이미지 구성 방식

하나의 outfit sample은 여러 개의 fashion item 이미지로 구성된다.

이번 baseline에서는 여러 item 이미지를 하나의 `3x3 grid image`로 합쳐 CNN 모델에 입력하였다.

```text
maximum items: 9
cell size: 224 x 224
grid size: 3 x 3
final grid image size: 672 x 672
empty cells: white padding
```

학습 시에는 생성된 grid image를 `224 x 224`로 resize하여 pretrained CNN backbone에 입력하였다.

이 방식은 outfit 조합을 하나의 이미지 분류 문제로 단순화할 수 있다는 장점이 있지만, item 간 관계를 명시적으로 모델링하지 못한다는 한계가 있다.

---

## 6. Train / Validation Split

최종 데이터셋은 stratified sampling을 사용하여 train과 validation으로 분할하였다.

```text
train: 80%
validation: 20%
```

분할 결과는 다음과 같다.

| split | incompatible | compatible | total |
|---|---:|---:|---:|
| train | 1,025 | 911 | 1,936 |
| validation | 256 | 228 | 484 |

train과 validation 모두 label 비율이 유사하게 유지되었다.

---

## 7. 모델 구성

baseline 모델은 ImageNet pretrained ResNet18을 사용하였다.

```text
backbone: ResNet18
pretrained weights: ImageNet
classifier: Linear(512 → 2)
training method: full fine-tuning
loss: CrossEntropyLoss
optimizer: Adam
learning rate: 1e-4
batch size: 16
epochs: 5
```

ResNet18은 최종 모델 후보가 아니라, 착장 조화 분류 가능성을 확인하기 위한 기준 baseline으로 사용하였다.

---

## 8. 학습 결과

ResNet18 baseline 학습 결과는 다음과 같다.

| epoch | train_loss | train_acc | val_loss | val_acc |
|---:|---:|---:|---:|---:|
| 1 | 0.6431 | 0.6410 | 0.6334 | 0.6591 |
| 2 | 0.3743 | 0.8347 | 0.7287 | 0.6508 |
| 3 | 0.1986 | 0.9210 | 1.0492 | 0.6818 |
| 4 | 0.1640 | 0.9427 | 1.1763 | 0.6736 |
| 5 | 0.1437 | 0.9427 | 0.9351 | 0.6798 |

최고 validation accuracy는 다음과 같다.

```text
Best validation accuracy: 0.6818
```

---

## 9. 결과 해석

ResNet18 grid baseline은 최고 validation accuracy `68.18%`를 기록하였다.

이 데이터셋에서 다수 클래스인 label 0만 예측했을 때의 기준 성능은 약 `52.9%`이다.

```text
majority-class baseline: approximately 52.9%
ResNet18 best validation accuracy: 68.18%
```

따라서 ResNet18 baseline은 다수 클래스 기준선보다 높은 성능을 보였고, 구성한 데이터셋에서 착장 조화 분류가 어느 정도 학습 가능하다는 것을 확인하였다.

하지만 train accuracy는 94% 이상까지 상승한 반면, validation accuracy는 68% 수준에 머물렀다. 이는 모델이 train set에는 과하게 맞춰졌지만, validation set에 대해서는 충분히 일반화하지 못했다는 것을 의미한다.

---

## 10. Experiment 01과의 차이

Experiment 01의 AVA baseline은 일반 이미지의 aesthetic score를 기준으로 high / low를 분류한 실험이었다.

당시에는 애매한 중간 점수 이미지를 제외하였다.

```text
low: score <= 4.0
high: score >= 6.5
middle-score images: excluded
```

반면 Experiment 02의 outfit compatibility 분류는 여러 fashion item 간의 조화를 판단해야 하는 문제이다.

모델은 단순히 이미지가 예쁜지 보는 것이 아니라 다음 요소들을 함께 고려해야 한다.

```text
item relationship
color harmony
style consistency
category combination
overall outfit balance
```

따라서 AVA baseline보다 validation accuracy가 낮게 나온 것은 자연스러운 결과로 볼 수 있다.

---

## 11. 한계점

이번 ResNet18 grid baseline에는 다음과 같은 한계가 있다.

첫째, 이미지까지 모두 매칭된 최종 dataset이 2,420개로 크지 않다.

둘째, 여러 item 이미지를 하나의 grid image로 붙이는 방식은 item 간 관계를 명시적으로 표현하지 못한다.

셋째, ResNet18 full fine-tuning은 작은 dataset에서 빠르게 overfitting되는 경향을 보였다.

넷째, outfit compatibility label은 AVA high / low label보다 더 애매할 수 있다.

---

## 12. 결론

Experiment 02에서는 xthan Polyvore의 compatibility label과 Marqo Polyvore의 item image를 결합하여 착장 조화 분류 dataset을 구성하였다.

최종적으로 2,420개의 outfit grid image dataset을 생성하였고, label 0과 label 1의 비율이 비교적 균형적인 것을 확인하였다.

ResNet18 full fine-tuning baseline은 최고 validation accuracy `68.18%`를 기록하였다. 이는 majority-class baseline보다 높은 성능으로, 착장 조화 분류 문제가 어느 정도 학습 가능하다는 것을 보여준다.

하지만 train accuracy와 validation accuracy의 차이가 커서 과적합 경향이 확인되었다. 따라서 단순 grid image 입력과 ResNet18 full fine-tuning만으로는 착장 조화 평가를 충분히 모델링하기 어렵다고 판단하였다.

Experiment 02는 최종 성능을 높이는 실험이 아니라, 착장 미감 평가 문제로 넘어가기 위한 feasibility-check baseline으로 정리할 수 있다.

---

## 13. 다음 단계

다음 단계에서는 더 적합한 backbone과 feature representation을 비교한다.

```text
1. validation confusion matrix 확인
2. EfficientNet-B0 비교
3. ConvNeXt-Tiny 비교
4. CLIP image encoder 기반 item-level feature fusion 적용
5. 이후 MobileNetV3 또는 EfficientNet-B0 기반 경량화 모델 검토
```

전체 실험 흐름은 다음과 같다.

```text
Experiment 02
→ Polyvore 기반 착장 조화 분류 가능성 확인

Experiment 03
→ CLIP 기반 성능 개선

Experiment 04
→ 설명 가능한 피드백 구조 설계

Experiment 05
→ 경량화 모델 검토
```