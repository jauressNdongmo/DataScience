package com.agri.agriData.api;

import java.util.Map;

public record ApiError(
        String code,
        String message,
        Map<String, Object> details,
        String correlationId
) {
}
