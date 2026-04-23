package com.agri.decision.dto;

import java.util.List;
import java.util.Map;

public record DecisionResponse(
        String country,
        String crop,
        int year,
        double predictedYield,
        String modelVersion,
        Integer dataYearMin,
        Integer dataYearMax,
        double weatherRisk,
        double marketIndex,
        double ndviIndex,
        double riskScore,
        String riskLevel,
        double confidence,
        boolean degradedMode,
        long signalFreshnessSeconds,
        Map<String, Double> contributions,
        Map<String, String> sources,
        List<String> warnings,
        List<String> recommendations
) {
}
