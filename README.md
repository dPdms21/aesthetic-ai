# Aesthetic AI

> 이미지 기반 미적 품질 평가 및 설명 가능한 피드백 생성을 위한 AI 연구 프로젝트

## Project Goal

본 프로젝트는 이미지를 입력으로 받아 미적 품질을 점수화하고, 사용자가 이해할 수 있는 피드백을 제공하는 설명 가능한 시각 미감 평가 AI를 구현하는 것을 목표로 한다.

초기 연구 대상은 착장 사진의 미적 평가이며, 이후 장소 기반 코디 추천, UI/PPT/인테리어 피드백 등 다양한 시각 결과물 평가 영역으로 확장할 수 있다.

## Main Scope

- AVA(Aesthetic Visual Analysis) 데이터셋 기반 미적 점수 예측
- 경량 CNN 기반 baseline 모델 구현
- Low / Medium / High 등급 분류 실험
- 구도, 색감, 밝기, 배경 복잡도 기반 설명 가능한 피드백 설계
- Raspberry Pi 기반 경량 추론 가능성 검토

## Development Plan

1. AVA 데이터셋 구조 확인
2. 재현 가능한 subset 생성
3. Baseline 모델 학습
4. 미적 점수/등급 예측
5. 설명 가능한 피드백 모듈 설계
6. 웹 데모 및 Raspberry Pi 적용 가능성 검토