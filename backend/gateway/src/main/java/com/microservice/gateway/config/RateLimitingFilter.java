package com.microservice.gateway.config;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class RateLimitingFilter implements GlobalFilter, Ordered {

    private static final String H_CORRELATION_ID = "X-Correlation-Id";
    private static final String H_USER_ID = "X-User-Id";
    private static final String H_TENANT_ID = "X-Tenant-Id";

    private final GatewayRateLimitProperties rateLimitProperties;
    private final ObjectMapper objectMapper;
    private final Counter rejectedCounter;
    private final ConcurrentHashMap<String, CounterWindow> counters = new ConcurrentHashMap<>();

    public RateLimitingFilter(
            GatewayRateLimitProperties rateLimitProperties,
            ObjectMapper objectMapper,
            MeterRegistry meterRegistry
    ) {
        this.rateLimitProperties = rateLimitProperties;
        this.objectMapper = objectMapper;
        this.rejectedCounter = Counter.builder("gateway.rate_limit.rejected.total")
                .description("Nombre total de requêtes rejetées par le rate limiting")
                .register(meterRegistry);
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        if (!rateLimitProperties.isEnabled()) {
            return chain.filter(exchange);
        }

        String path = exchange.getRequest().getPath().value();
        if (path.startsWith("/actuator")) {
            return chain.filter(exchange);
        }

        String key = resolveKey(exchange);
        long now = System.currentTimeMillis();
        long windowMs = rateLimitProperties.getWindowSeconds() * 1000L;
        int requestCount = counters.compute(key, (ignored, current) -> {
            if (current == null || now - current.windowStartEpochMs >= windowMs) {
                return new CounterWindow(now, 1);
            }
            current.count += 1;
            return current;
        }).count;

        if (requestCount <= rateLimitProperties.getRequestsPerWindow()) {
            return chain.filter(exchange);
        }

        rejectedCounter.increment();
        String correlationId = exchange.getRequest().getHeaders().getFirst(H_CORRELATION_ID);
        return writeError(exchange.getResponse(), HttpStatus.TOO_MANY_REQUESTS, "RATE_LIMIT_EXCEEDED",
                correlationId,
                "Le quota de requêtes est dépassé pour cette fenêtre.");
    }

    @Override
    public int getOrder() {
        return -1000;
    }

    private String resolveKey(ServerWebExchange exchange) {
        String tenant = exchange.getRequest().getHeaders().getFirst(H_TENANT_ID);
        String user = exchange.getRequest().getHeaders().getFirst(H_USER_ID);
        String remote = exchange.getRequest().getRemoteAddress() != null
                ? exchange.getRequest().getRemoteAddress().getAddress().getHostAddress()
                : "unknown-ip";

        if (tenant != null && !tenant.isBlank()) {
            if (user != null && !user.isBlank()) {
                return "tenant:" + tenant + "|user:" + user;
            }
            return "tenant:" + tenant;
        }
        return "ip:" + remote;
    }

    private Mono<Void> writeError(
            ServerHttpResponse response,
            HttpStatus status,
            String code,
            String correlationId,
            String message
    ) {
        response.setStatusCode(status);
        response.getHeaders().setContentType(MediaType.APPLICATION_JSON);
        response.getHeaders().set("Cache-Control", "no-store");
        if (correlationId != null && !correlationId.isBlank()) {
            response.getHeaders().set(H_CORRELATION_ID, correlationId);
        }
        GatewayErrorPayload payload = new GatewayErrorPayload(
                code,
                message,
                Map.of("timestamp", Instant.now().toString()),
                correlationId
        );

        try {
            byte[] bytes = objectMapper.writeValueAsString(payload).getBytes(StandardCharsets.UTF_8);
            DataBuffer buffer = response.bufferFactory().wrap(bytes);
            return response.writeWith(Mono.just(buffer));
        } catch (JsonProcessingException e) {
            byte[] bytes = ("{\"code\":\"" + code + "\",\"message\":\"" + message + "\"}")
                    .getBytes(StandardCharsets.UTF_8);
            DataBuffer buffer = response.bufferFactory().wrap(bytes);
            return response.writeWith(Mono.just(buffer));
        }
    }

    private static final class CounterWindow {
        private final long windowStartEpochMs;
        private int count;

        private CounterWindow(long windowStartEpochMs, int count) {
            this.windowStartEpochMs = windowStartEpochMs;
            this.count = count;
        }
    }
}
