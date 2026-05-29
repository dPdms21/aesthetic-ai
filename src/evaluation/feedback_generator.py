# src/evaluation/feedback_generator.py

import json
from pathlib import Path
from typing import Dict, Any, List


def clamp_score(score: float) -> int:
    """
    점수를 0~100 범위로 제한하고 정수로 변환한다.
    """
    return int(round(max(0, min(100, score))))


def probability_to_score(compatible_probability: float) -> int:
    """
    compatible 예측 확률을 사용자용 전체 점수로 변환한다.
    """
    return clamp_score(compatible_probability * 100)


def get_score_level(score: int) -> str:
    """
    점수 구간을 피드백 생성을 위한 level로 변환한다.
    """
    if score >= 80:
        return "high"
    if score >= 60:
        return "medium"
    if score >= 40:
        return "low"
    return "very_low"


def get_prediction_label(compatible_probability: float, threshold: float = 0.5) -> str:
    """
    compatible 확률을 기준으로 예측 label을 반환한다.
    """
    if compatible_probability >= threshold:
        return "compatible"
    return "incompatible"


def get_confidence(compatible_probability: float) -> float:
    """
    예측 class에 대한 confidence를 계산한다.
    """
    confidence = max(compatible_probability, 1 - compatible_probability)
    return round(confidence, 4)


def calculate_color_harmony_score(color_stats: Dict[str, float]) -> int:
    """
    color harmony stats를 기반으로 색감 조화 점수를 계산한다.

    보정된 규칙:
    - RGB 평균 거리와 HSV 표준편차가 낮을수록 색감이 안정적이라고 본다.
    - 기존 계산식보다 감점을 완화하여, 좋은 색감 sample이 80점 이상으로 나올 수 있게 조정한다.
    """

    rgb_mean_distance = color_stats.get("rgb_mean_distance", 0.3)
    rgb_std_distance = color_stats.get("rgb_std_distance", 0.1)
    hue_std = color_stats.get("hue_std", 0.15)
    saturation_std = color_stats.get("saturation_std", 0.2)
    value_std = color_stats.get("value_std", 0.2)

    score = 100

    score -= rgb_mean_distance * 55
    score -= rgb_std_distance * 40
    score -= hue_std * 35
    score -= saturation_std * 25
    score -= value_std * 20

    return clamp_score(score)


def calculate_item_relation_score(pairwise_stats: Dict[str, float]) -> int:
    """
    pairwise relation stats를 기반으로 아이템 간 조화도 점수를 계산한다.

    현재 규칙:
    - item embedding 간 평균 유사도가 높을수록 점수가 높다.
    - 최소 유사도가 낮거나 유사도 편차/range가 크면 감점한다.
    """

    mean_similarity = pairwise_stats.get("mean_similarity", 0.5)
    min_similarity = pairwise_stats.get("min_similarity", 0.3)
    std_similarity = pairwise_stats.get("std_similarity", 0.1)
    range_similarity = pairwise_stats.get("range_similarity", 0.3)
    num_items_scaled = pairwise_stats.get("num_items_scaled", 0.5)

    score = 40

    score += mean_similarity * 45
    score += min_similarity * 20
    score += num_items_scaled * 10
    score -= std_similarity * 35
    score -= range_similarity * 25

    return clamp_score(score)


def calculate_style_consistency_score(category_stats: Dict[str, Dict[str, float]]) -> int:
    """
    category-aware relation stats를 기반으로 스타일 통일감 점수를 계산한다.

    현재 규칙:
    - 사용 가능한 category pair의 평균 유사도를 기반으로 점수를 계산한다.
    - 주요 조합인 top-bottom, main-shoes, bottom-shoes에는 더 큰 가중치를 둔다.
    """

    pair_weights = {
        "main_shoes": 1.3,
        "accessory_main": 0.8,
        "bag_main": 0.9,
        "outer_main": 1.0,
        "top_shoes": 1.1,
        "bottom_shoes": 1.2,
        "top_bottom": 1.4,
        "dress_shoes": 1.2,
    }

    weighted_sum = 0.0
    weight_total = 0.0

    for pair_name, weight in pair_weights.items():
        pair_stat = category_stats.get(pair_name)

        if not pair_stat:
            continue

        available = pair_stat.get("available", 0)

        if available != 1:
            continue

        mean_similarity = pair_stat.get("mean_similarity", 0.5)
        min_similarity = pair_stat.get("min_similarity", 0.3)
        std_similarity = pair_stat.get("std_similarity", 0.1)

        pair_score = 50
        pair_score += mean_similarity * 40
        pair_score += min_similarity * 15
        pair_score -= std_similarity * 25

        weighted_sum += pair_score * weight
        weight_total += weight

    if weight_total == 0:
        return 50

    return clamp_score(weighted_sum / weight_total)


def generate_summary_feedback(overall_score: int) -> str:
    """
    전체 점수 기반 요약 피드백을 생성한다.
    """
    level = get_score_level(overall_score)

    feedback_map = {
        "high": "전체적으로 아이템 간 조화가 좋은 착장입니다.",
        "medium": "전반적으로 무난하고 안정적인 착장입니다.",
        "low": "일부 아이템 조합에서 어색함이 느껴질 수 있습니다.",
        "very_low": "전체적인 조화가 부족해 보일 수 있는 착장입니다.",
    }

    return feedback_map[level]


def generate_color_feedback(color_score: int) -> str:
    """
    색감 조화 점수 기반 피드백을 생성한다.
    """
    level = get_score_level(color_score)

    feedback_map = {
        "high": "색감 조합이 안정적이며 전체 톤이 자연스럽게 어울립니다.",
        "medium": "색감은 전반적으로 무난하지만 일부 색상 대비가 살짝 느껴질 수 있습니다.",
        "low": "일부 색상이 전체 착장과 자연스럽게 연결되지 않을 수 있습니다.",
        "very_low": "색 조합에서 다소 충돌이 느껴질 수 있습니다.",
    }

    return feedback_map[level]


def generate_item_relation_feedback(item_relation_score: int) -> str:
    """
    아이템 간 관계 점수 기반 피드백을 생성한다.
    """
    level = get_score_level(item_relation_score)

    feedback_map = {
        "high": "아이템 간 시각적 관계가 자연스럽고 조합이 잘 맞습니다.",
        "medium": "대부분의 아이템은 잘 어울리지만 일부 조합은 조금 약할 수 있습니다.",
        "low": "몇몇 아이템이 하나의 착장으로 자연스럽게 연결되지 않을 수 있습니다.",
        "very_low": "아이템 간 조화가 부족해 전체 착장이 분리되어 보일 수 있습니다.",
    }

    return feedback_map[level]


def generate_style_feedback(style_score: int) -> str:
    """
    스타일 통일감 점수 기반 피드백을 생성한다.
    """
    level = get_score_level(style_score)

    feedback_map = {
        "high": "상의, 하의, 신발 등 주요 카테고리 간 스타일 통일감이 좋은 편입니다.",
        "medium": "전체적인 스타일 방향은 대체로 일관적입니다.",
        "low": "일부 아이템의 스타일 방향이 서로 다르게 느껴질 수 있습니다.",
        "very_low": "착장의 스타일 방향이 명확하지 않아 통일감이 약해 보일 수 있습니다.",
    }

    return feedback_map[level]


def build_feedback_result(
    sample_id: int,
    compatible_probability: float,
    color_stats: Dict[str, float],
    pairwise_stats: Dict[str, float],
    category_stats: Dict[str, Dict[str, float]],
) -> Dict[str, Any]:
    """
    하나의 착장 sample에 대한 최종 피드백 결과를 생성한다.
    """

    overall_score = probability_to_score(compatible_probability)
    color_score = calculate_color_harmony_score(color_stats)
    relation_score = calculate_item_relation_score(pairwise_stats)
    style_score = calculate_style_consistency_score(category_stats)

    result = {
        "sample_id": sample_id,
        "overall_score": overall_score,
        "color_harmony_score": color_score,
        "item_relation_score": relation_score,
        "style_consistency_score": style_score,
        "prediction": get_prediction_label(compatible_probability),
        "confidence": get_confidence(compatible_probability),
        "summary_feedback": generate_summary_feedback(overall_score),
        "color_feedback": generate_color_feedback(color_score),
        "item_relation_feedback": generate_item_relation_feedback(relation_score),
        "style_feedback": generate_style_feedback(style_score),
    }

    return result


def save_feedback_samples(
    feedback_results: List[Dict[str, Any]],
    output_path: str = "results/experiment_04_feedback_samples.json",
) -> None:
    """
    여러 sample의 피드백 결과를 json 파일로 저장한다.
    """

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(feedback_results, f, ensure_ascii=False, indent=2)

    print(f"Saved feedback samples to: {output_file}")


if __name__ == "__main__":
    sample_inputs = [
        {
            "sample_id": 0,
            "compatible_probability": 0.8285,
            "color_stats": {
                "rgb_mean_distance": 0.18,
                "rgb_std_distance": 0.08,
                "hue_std": 0.10,
                "saturation_std": 0.16,
                "value_std": 0.14,
            },
            "pairwise_stats": {
                "mean_similarity": 0.78,
                "min_similarity": 0.62,
                "std_similarity": 0.08,
                "range_similarity": 0.22,
                "num_items_scaled": 0.7,
            },
            "category_stats": {
                "top_bottom": {
                    "available": 1,
                    "mean_similarity": 0.82,
                    "min_similarity": 0.70,
                    "std_similarity": 0.07,
                },
                "main_shoes": {
                    "available": 1,
                    "mean_similarity": 0.80,
                    "min_similarity": 0.66,
                    "std_similarity": 0.08,
                },
                "bag_main": {
                    "available": 1,
                    "mean_similarity": 0.72,
                    "min_similarity": 0.58,
                    "std_similarity": 0.10,
                },
            },
        },
        {
            "sample_id": 1,
            "compatible_probability": 0.7128,
            "color_stats": {
                "rgb_mean_distance": 0.26,
                "rgb_std_distance": 0.10,
                "hue_std": 0.16,
                "saturation_std": 0.20,
                "value_std": 0.18,
            },
            "pairwise_stats": {
                "mean_similarity": 0.68,
                "min_similarity": 0.50,
                "std_similarity": 0.11,
                "range_similarity": 0.30,
                "num_items_scaled": 0.6,
            },
            "category_stats": {
                "top_bottom": {
                    "available": 1,
                    "mean_similarity": 0.70,
                    "min_similarity": 0.55,
                    "std_similarity": 0.10,
                },
                "main_shoes": {
                    "available": 1,
                    "mean_similarity": 0.66,
                    "min_similarity": 0.52,
                    "std_similarity": 0.12,
                },
            },
        },
        {
            "sample_id": 2,
            "compatible_probability": 0.4380,
            "color_stats": {
                "rgb_mean_distance": 0.42,
                "rgb_std_distance": 0.18,
                "hue_std": 0.26,
                "saturation_std": 0.30,
                "value_std": 0.24,
            },
            "pairwise_stats": {
                "mean_similarity": 0.48,
                "min_similarity": 0.28,
                "std_similarity": 0.18,
                "range_similarity": 0.42,
                "num_items_scaled": 0.5,
            },
            "category_stats": {
                "top_bottom": {
                    "available": 1,
                    "mean_similarity": 0.48,
                    "min_similarity": 0.30,
                    "std_similarity": 0.18,
                },
                "main_shoes": {
                    "available": 1,
                    "mean_similarity": 0.45,
                    "min_similarity": 0.26,
                    "std_similarity": 0.20,
                },
            },
        },
        {
            "sample_id": 3,
            "compatible_probability": 0.2760,
            "color_stats": {
                "rgb_mean_distance": 0.55,
                "rgb_std_distance": 0.24,
                "hue_std": 0.34,
                "saturation_std": 0.38,
                "value_std": 0.32,
            },
            "pairwise_stats": {
                "mean_similarity": 0.32,
                "min_similarity": 0.14,
                "std_similarity": 0.24,
                "range_similarity": 0.58,
                "num_items_scaled": 0.4,
            },
            "category_stats": {
                "top_bottom": {
                    "available": 1,
                    "mean_similarity": 0.30,
                    "min_similarity": 0.12,
                    "std_similarity": 0.24,
                },
                "main_shoes": {
                    "available": 1,
                    "mean_similarity": 0.28,
                    "min_similarity": 0.10,
                    "std_similarity": 0.26,
                },
            },
        },
        {
            "sample_id": 4,
            "compatible_probability": 0.9050,
            "color_stats": {
                "rgb_mean_distance": 0.12,
                "rgb_std_distance": 0.05,
                "hue_std": 0.07,
                "saturation_std": 0.10,
                "value_std": 0.09,
            },
            "pairwise_stats": {
                "mean_similarity": 0.86,
                "min_similarity": 0.74,
                "std_similarity": 0.05,
                "range_similarity": 0.16,
                "num_items_scaled": 0.8,
            },
            "category_stats": {
                "top_bottom": {
                    "available": 1,
                    "mean_similarity": 0.88,
                    "min_similarity": 0.78,
                    "std_similarity": 0.05,
                },
                "main_shoes": {
                    "available": 1,
                    "mean_similarity": 0.84,
                    "min_similarity": 0.72,
                    "std_similarity": 0.06,
                },
                "bag_main": {
                    "available": 1,
                    "mean_similarity": 0.80,
                    "min_similarity": 0.68,
                    "std_similarity": 0.07,
                },
            },
        },
    ]

    feedback_results = [
        build_feedback_result(
            sample_id=sample["sample_id"],
            compatible_probability=sample["compatible_probability"],
            color_stats=sample["color_stats"],
            pairwise_stats=sample["pairwise_stats"],
            category_stats=sample["category_stats"],
        )
        for sample in sample_inputs
    ]

    for result in feedback_results:
        print(result)

    save_feedback_samples(feedback_results)