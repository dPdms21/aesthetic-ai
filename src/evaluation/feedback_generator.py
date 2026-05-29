# src/evaluation/feedback_generator.py

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd


CATEGORY_PAIRS = [
    "top_bottom",
    "main_shoes",
    "bottom_shoes",
    "top_shoes",
    "bag_main",
    "outer_main",
    "accessory_main",
    "dress_shoes",
]


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


def get_color_reason(color_stats: Dict[str, float]) -> str:
    """
    color stats 중 가장 큰 감점 원인을 찾아 색감 피드백 이유를 생성한다.
    """

    penalty_map = {
        "rgb_mean_distance": color_stats.get("rgb_mean_distance", 0.3) * 55,
        "rgb_std_distance": color_stats.get("rgb_std_distance", 0.1) * 40,
        "hue_std": color_stats.get("hue_std", 0.15) * 35,
        "saturation_std": color_stats.get("saturation_std", 0.2) * 25,
        "value_std": color_stats.get("value_std", 0.2) * 20,
    }

    main_factor = max(penalty_map, key=penalty_map.get)

    reason_map = {
        "rgb_mean_distance": "아이템 간 전체적인 색 차이가 큰 편입니다.",
        "rgb_std_distance": "아이템별 색 차이의 편차가 있어 일부 색상이 따로 보일 수 있습니다.",
        "hue_std": "색상 톤의 변화가 커서 전체 색감이 분산되어 보일 수 있습니다.",
        "saturation_std": "채도 차이가 있어 일부 아이템이 더 튀어 보일 수 있습니다.",
        "value_std": "밝기 차이가 있어 착장의 톤 균형이 약해 보일 수 있습니다.",
    }

    return reason_map[main_factor]


def get_item_relation_reason(pairwise_stats: Dict[str, float]) -> str:
    """
    pairwise relation stats를 기반으로 아이템 관계 피드백 이유를 생성한다.
    """

    mean_similarity = pairwise_stats.get("mean_similarity", 0.5)
    min_similarity = pairwise_stats.get("min_similarity", 0.3)
    std_similarity = pairwise_stats.get("std_similarity", 0.1)
    range_similarity = pairwise_stats.get("range_similarity", 0.3)

    if min_similarity < 0.25:
        return "일부 아이템 pair의 유사도가 낮아 특정 아이템이 전체 착장과 분리되어 보일 수 있습니다."

    if range_similarity > 0.45:
        return "아이템 간 유사도 차이가 커서 조합의 일관성이 약해질 수 있습니다."

    if std_similarity > 0.18:
        return "아이템 간 관계의 편차가 있어 일부 조합은 자연스럽지 않을 수 있습니다."

    if mean_similarity >= 0.75:
        return "전체 아이템 간 평균 유사도가 높아 하나의 착장으로 자연스럽게 연결됩니다."

    return "전체적인 아이템 관계는 무난하지만, 일부 조합은 더 강한 연결감이 필요할 수 있습니다."


def get_style_reason(category_stats: Dict[str, Dict[str, float]]) -> str:
    """
    category-aware relation stats에서 가장 약한 category pair를 찾아 스타일 피드백 이유를 생성한다.
    """

    pair_display_names = {
        "top_bottom": "상의와 하의",
        "main_shoes": "주요 의상과 신발",
        "bottom_shoes": "하의와 신발",
        "top_shoes": "상의와 신발",
        "bag_main": "가방과 주요 의상",
        "outer_main": "아우터와 주요 의상",
        "accessory_main": "액세서리와 주요 의상",
        "dress_shoes": "드레스와 신발",
    }

    available_pairs = []

    for pair_name, pair_stat in category_stats.items():
        if pair_stat.get("available", 0) != 1:
            continue

        mean_similarity = pair_stat.get("mean_similarity", 0.5)
        min_similarity = pair_stat.get("min_similarity", 0.3)
        std_similarity = pair_stat.get("std_similarity", 0.1)

        pair_score = 50
        pair_score += mean_similarity * 40
        pair_score += min_similarity * 15
        pair_score -= std_similarity * 25

        available_pairs.append((pair_name, pair_score, mean_similarity, min_similarity, std_similarity))

    if not available_pairs:
        return "비교 가능한 주요 카테고리 조합이 부족해 스타일 통일감을 중립적으로 평가했습니다."

    weakest_pair = min(available_pairs, key=lambda x: x[1])
    strongest_pair = max(available_pairs, key=lambda x: x[1])

    weakest_name = pair_display_names.get(weakest_pair[0], weakest_pair[0])
    strongest_name = pair_display_names.get(strongest_pair[0], strongest_pair[0])

    if weakest_pair[1] < 60:
        return f"{weakest_name} 조합의 유사도가 낮아 해당 부분에서 스타일 방향이 다르게 느껴질 수 있습니다."

    if strongest_pair[1] >= 85:
        return f"{strongest_name} 조합이 안정적이어서 전체 스타일 통일감에 긍정적으로 작용합니다."

    return f"{weakest_name} 조합은 상대적으로 약하지만, 전체적인 스타일 방향은 크게 벗어나지 않습니다."


def generate_detailed_feedback(
    overall_score: int,
    color_score: int,
    relation_score: int,
    style_score: int,
) -> str:
    """
    가장 약한 하위 점수를 기준으로 종합 보완 피드백을 생성한다.
    """

    score_map = {
        "color": color_score,
        "relation": relation_score,
        "style": style_score,
    }

    weakest_area = min(score_map, key=score_map.get)

    if overall_score >= 80:
        if weakest_area == "color":
            return "전체적인 착장 조화는 좋지만, 색감 연결을 조금 더 정리하면 완성도가 더 높아질 수 있습니다."
        if weakest_area == "relation":
            return "전체적으로 조화로운 착장이지만, 일부 아이템 간 연결감을 보완하면 더 자연스러워질 수 있습니다."
        return "전체적인 완성도는 높지만, 일부 카테고리 조합의 스타일 방향을 맞추면 더 안정적인 착장이 될 수 있습니다."

    if overall_score >= 60:
        if weakest_area == "color":
            return "전반적으로 무난한 착장이지만, 색 조합이 가장 큰 보완 포인트로 보입니다."
        if weakest_area == "relation":
            return "전반적인 착장은 안정적이나, 일부 아이템 조합의 연결성이 다소 약할 수 있습니다."
        return "전반적으로 무난하지만, 스타일 방향을 조금 더 통일하면 더 완성도 있는 착장이 될 수 있습니다."

    if weakest_area == "color":
        return "전체 조화가 약한 편이며, 특히 색감 연결을 먼저 정리하는 것이 좋습니다."
    if weakest_area == "relation":
        return "전체 조화가 약한 편이며, 아이템 간 관계가 자연스럽게 이어지도록 조합을 조정하는 것이 좋습니다."
    return "전체 조화가 약한 편이며, 착장의 스타일 방향을 더 명확히 잡는 것이 좋습니다."


def calculate_color_harmony_score(color_stats: Dict[str, float]) -> int:
    """
    color harmony stats를 기반으로 색감 조화 점수를 계산한다.

    규칙:
    - RGB 평균 거리와 HSV 표준편차가 낮을수록 색감이 안정적이라고 본다.
    - 색 차이와 hue/saturation/value 변동이 클수록 감점한다.
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

    규칙:
    - item embedding 간 평균 유사도와 최소 유사도가 높을수록 점수가 높다.
    - 유사도 표준편차와 range가 크면 일부 아이템이 튈 가능성이 있다고 보고 감점한다.
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

    규칙:
    - 사용 가능한 category pair의 유사도를 기반으로 점수를 계산한다.
    - top-bottom, main-shoes, bottom-shoes처럼 착장 인상에 중요한 조합에는 더 큰 가중치를 둔다.
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


def generate_color_feedback(color_score: int, color_stats: Dict[str, float]) -> str:
    """
    색감 조화 점수와 color stats 기반 피드백을 생성한다.
    """
    level = get_score_level(color_score)
    reason = get_color_reason(color_stats)

    feedback_map = {
        "high": f"색감 조합이 안정적이며 전체 톤이 자연스럽게 어울립니다. {reason}",
        "medium": f"색감은 전반적으로 무난하지만 일부 색상 대비가 느껴질 수 있습니다. {reason}",
        "low": f"일부 색상이 전체 착장과 자연스럽게 연결되지 않을 수 있습니다. {reason}",
        "very_low": f"색 조합에서 다소 충돌이 느껴질 수 있습니다. {reason}",
    }

    return feedback_map[level]


def generate_item_relation_feedback(
    item_relation_score: int,
    pairwise_stats: Dict[str, float],
) -> str:
    """
    아이템 간 관계 점수와 pairwise stats 기반 피드백을 생성한다.
    """
    level = get_score_level(item_relation_score)
    reason = get_item_relation_reason(pairwise_stats)

    feedback_map = {
        "high": f"아이템 간 시각적 관계가 자연스럽고 조합이 잘 맞습니다. {reason}",
        "medium": f"대부분의 아이템은 잘 어울리지만 일부 조합은 조금 약할 수 있습니다. {reason}",
        "low": f"몇몇 아이템이 하나의 착장으로 자연스럽게 연결되지 않을 수 있습니다. {reason}",
        "very_low": f"아이템 간 조화가 부족해 전체 착장이 분리되어 보일 수 있습니다. {reason}",
    }

    return feedback_map[level]


def generate_style_feedback(
    style_score: int,
    category_stats: Dict[str, Dict[str, float]],
) -> str:
    """
    스타일 통일감 점수와 category-aware relation stats 기반 피드백을 생성한다.
    """
    level = get_score_level(style_score)
    reason = get_style_reason(category_stats)

    feedback_map = {
        "high": f"주요 카테고리 간 스타일 통일감이 좋은 편입니다. {reason}",
        "medium": f"전체적인 스타일 방향은 대체로 일관적입니다. {reason}",
        "low": f"일부 아이템의 스타일 방향이 서로 다르게 느껴질 수 있습니다. {reason}",
        "very_low": f"착장의 스타일 방향이 명확하지 않아 통일감이 약해 보일 수 있습니다. {reason}",
    }

    return feedback_map[level]


def row_to_feature_dicts(row: pd.Series) -> Dict[str, Dict[str, Any]]:
    """
    validation feedback input csv의 한 행을
    color_stats, pairwise_stats, category_stats 구조로 변환한다.
    """

    color_stats = {
        "rgb_mean_distance": float(row["rgb_mean_distance"]),
        "rgb_std_distance": float(row["rgb_std_distance"]),
        "hue_std": float(row["hue_std"]),
        "saturation_std": float(row["saturation_std"]),
        "value_std": float(row["value_std"]),
    }

    pairwise_stats = {
        "mean_similarity": float(row["mean_similarity"]),
        "min_similarity": float(row["min_similarity"]),
        "std_similarity": float(row["std_similarity"]),
        "range_similarity": float(row["range_similarity"]),
        "num_items_scaled": float(row["num_items_scaled"]),
    }

    category_stats = {}

    for pair_name in CATEGORY_PAIRS:
        category_stats[pair_name] = {
            "available": int(row[f"{pair_name}_available"]),
            "mean_similarity": float(row[f"{pair_name}_mean_similarity"]),
            "min_similarity": float(row[f"{pair_name}_min_similarity"]),
            "std_similarity": float(row[f"{pair_name}_std_similarity"]),
        }

    return {
        "color_stats": color_stats,
        "pairwise_stats": pairwise_stats,
        "category_stats": category_stats,
    }


def build_feedback_result(
    sample_id: int,
    compatible_probability: float,
    color_stats: Dict[str, float],
    pairwise_stats: Dict[str, float],
    category_stats: Dict[str, Dict[str, float]],
    true_label: Optional[int] = None,
    pred_label: Optional[int] = None,
) -> Dict[str, Any]:
    """
    하나의 validation sample에 대한 최종 피드백 결과를 생성한다.
    """

    overall_score = probability_to_score(compatible_probability)
    color_score = calculate_color_harmony_score(color_stats)
    relation_score = calculate_item_relation_score(pairwise_stats)
    style_score = calculate_style_consistency_score(category_stats)

    result = {
        "sample_id": sample_id,
        "true_label": true_label,
        "pred_label": pred_label,
        "overall_score": overall_score,
        "color_harmony_score": color_score,
        "item_relation_score": relation_score,
        "style_consistency_score": style_score,
        "compatible_probability": round(compatible_probability, 4),
        "prediction": get_prediction_label(compatible_probability),
        "confidence": get_confidence(compatible_probability),
        "summary_feedback": generate_summary_feedback(overall_score),
        "color_feedback": generate_color_feedback(color_score, color_stats),
        "item_relation_feedback": generate_item_relation_feedback(relation_score, pairwise_stats),
        "style_feedback": generate_style_feedback(style_score, category_stats),
        "detailed_feedback": generate_detailed_feedback(
            overall_score=overall_score,
            color_score=color_score,
            relation_score=relation_score,
            style_score=style_score,
        ),
    }

    return result


def load_validation_feedback_inputs(
    input_path: str = "results/experiment_03_validation_feedback_inputs.csv",
) -> pd.DataFrame:
    """
    Experiment 03 validation feedback input csv를 읽는다.
    """

    input_file = Path(input_path)

    if not input_file.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_file}\n"
            "results/experiment_03_validation_feedback_inputs.csv 파일을 먼저 추가해야 합니다."
        )

    df = pd.read_csv(input_file)

    required_columns = [
        "sample_id",
        "true_label",
        "pred_label",
        "compatible_probability",
        "rgb_mean_distance",
        "rgb_std_distance",
        "hue_std",
        "saturation_std",
        "value_std",
        "mean_similarity",
        "min_similarity",
        "std_similarity",
        "range_similarity",
        "num_items_scaled",
    ]

    for pair_name in CATEGORY_PAIRS:
        required_columns.extend(
            [
                f"{pair_name}_available",
                f"{pair_name}_mean_similarity",
                f"{pair_name}_min_similarity",
                f"{pair_name}_std_similarity",
            ]
        )

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    return df


def generate_feedback_from_validation_csv(
    input_path: str = "results/experiment_03_validation_feedback_inputs.csv",
) -> List[Dict[str, Any]]:
    """
    Experiment 03 validation csv 전체에 대해 피드백 결과를 생성한다.
    """

    df = load_validation_feedback_inputs(input_path)
    feedback_results = []

    for _, row in df.iterrows():
        feature_dicts = row_to_feature_dicts(row)

        feedback_result = build_feedback_result(
            sample_id=int(row["sample_id"]),
            true_label=int(row["true_label"]),
            pred_label=int(row["pred_label"]),
            compatible_probability=float(row["compatible_probability"]),
            color_stats=feature_dicts["color_stats"],
            pairwise_stats=feature_dicts["pairwise_stats"],
            category_stats=feature_dicts["category_stats"],
        )

        feedback_results.append(feedback_result)

    return feedback_results


def save_feedback_samples(
    feedback_results: List[Dict[str, Any]],
    output_path: str,
) -> None:
    """
    여러 sample의 피드백 결과를 json 파일로 저장한다.
    """

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(feedback_results, f, ensure_ascii=False, indent=2)

    print(f"Saved feedback samples to: {output_file}")


def save_feedback_summary(
    feedback_results: List[Dict[str, Any]],
    output_path: str = "results/experiment_04_validation_feedback_summary.json",
) -> None:
    """
    생성된 validation feedback 결과의 간단한 요약 정보를 저장한다.
    """

    total_count = len(feedback_results)
    compatible_count = sum(1 for item in feedback_results if item["prediction"] == "compatible")
    incompatible_count = total_count - compatible_count

    avg_overall_score = sum(item["overall_score"] for item in feedback_results) / total_count
    avg_color_score = sum(item["color_harmony_score"] for item in feedback_results) / total_count
    avg_relation_score = sum(item["item_relation_score"] for item in feedback_results) / total_count
    avg_style_score = sum(item["style_consistency_score"] for item in feedback_results) / total_count

    summary = {
        "total_samples": total_count,
        "compatible_predictions": compatible_count,
        "incompatible_predictions": incompatible_count,
        "average_overall_score": round(avg_overall_score, 2),
        "average_color_harmony_score": round(avg_color_score, 2),
        "average_item_relation_score": round(avg_relation_score, 2),
        "average_style_consistency_score": round(avg_style_score, 2),
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"Saved feedback summary to: {output_file}")
    print(summary)


if __name__ == "__main__":
    input_csv_path = "results/experiment_03_validation_feedback_inputs.csv"
    output_json_path = "results/experiment_04_validation_feedback_samples.json"
    output_preview_path = "results/experiment_04_validation_feedback_preview.json"

    feedback_results = generate_feedback_from_validation_csv(input_csv_path)

    save_feedback_samples(
        feedback_results=feedback_results,
        output_path=output_json_path,
    )

    save_feedback_samples(
        feedback_results=feedback_results[:10],
        output_path=output_preview_path,
    )

    save_feedback_summary(feedback_results)

    print("\nPreview:")
    for result in feedback_results[:5]:
        print(result)