package com.agri.decision.dto;

public record PredictResponse(
        String model,
        String model_version,
        double predicted_yield,
        Integer year_min,
        Integer year_max
) {
}
