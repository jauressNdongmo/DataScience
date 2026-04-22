package com.agri.decision.dto;

public record PredictResponse(
        String model,
        double predicted_yield
) {
}
