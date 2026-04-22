package com.agri.decision.dto;

public record ExternalSignalResponse(
        String country,
        String crop,
        double weatherRiskScore,
        double marketPriceIndex,
        double ndviIndex
) {
}
