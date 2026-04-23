package com.agri.integration.dto;

import java.util.List;
import java.util.Map;

public record RealtimeSignalResponse(
        String country,
        String crop,
        double weatherRiskScore,
        double marketPriceIndex,
        double ndviIndex,
        String generatedAt,
        long signalFreshnessSeconds,
        boolean degraded,
        double confidence,
        Map<String, String> sources,
        List<String> warnings
) {
}
