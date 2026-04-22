package com.agri.integration.dto;

public record RealtimeSignalResponse(
        String country,
        String crop,
        double weatherRiskScore,
        double marketPriceIndex,
        double ndviIndex
) {
}
