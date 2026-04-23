package com.microservice.gateway.config;

import java.util.Map;

public record GatewayErrorPayload(
        String code,
        String message,
        Map<String, Object> details,
        String correlationId
) {
}
