package com.agri.decision.dto;

import java.util.List;

public record DecisionResponse(
        String country,
        String crop,
        int year,
        double predictedYield,
        double weatherRisk,
        double marketIndex,
        double ndviIndex,
        String riskLevel,
        List<String> recommendations
) {
}
