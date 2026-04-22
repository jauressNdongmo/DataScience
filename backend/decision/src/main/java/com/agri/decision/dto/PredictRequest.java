package com.agri.decision.dto;

public record PredictRequest(
        String country,
        String crop,
        int year,
        double rain_mm_per_year,
        double pesticides_tonnes,
        double temperature_c
) {
}
