package com.microservice.gateway.config;

import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Component
public class RequestContextFilter implements GlobalFilter, Ordered {

    private static final String H_CORRELATION_ID = "X-Correlation-Id";
    private static final String H_USER_ID = "X-User-Id";
    private static final String H_TENANT_ID = "X-Tenant-Id";
    private static final String H_USER_ROLES = "X-User-Roles";

    private final GatewaySecurityProperties securityProperties;

    public RequestContextFilter(GatewaySecurityProperties securityProperties) {
        this.securityProperties = securityProperties;
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String correlationId = resolveCorrelationId(exchange.getRequest());
        ServerWebExchange withCorrelation = mutateExchange(exchange, builder -> {
            if (!hasText(exchange.getRequest().getHeaders().getFirst(H_CORRELATION_ID))) {
                builder.header(H_CORRELATION_ID, correlationId);
            }
        });

        return chain.filter(applyDevIdentityIfMissing(withCorrelation));
    }

    @Override
    public int getOrder() {
        return -1100;
    }

    private ServerWebExchange applyDevIdentityIfMissing(ServerWebExchange exchange) {
        return mutateExchange(exchange, builder -> {
            if (!hasText(exchange.getRequest().getHeaders().getFirst(H_USER_ID))) {
                builder.header(H_USER_ID, securityProperties.getDevUserId());
            }
            if (!hasText(exchange.getRequest().getHeaders().getFirst(H_TENANT_ID))) {
                builder.header(H_TENANT_ID, securityProperties.getDevTenantId());
            }
            if (!hasText(exchange.getRequest().getHeaders().getFirst(H_USER_ROLES))) {
                builder.header(H_USER_ROLES, securityProperties.getDevRoles());
            }
        });
    }

    private ServerWebExchange mutateExchange(ServerWebExchange exchange, java.util.function.Consumer<ServerHttpRequest.Builder> mutator) {
        ServerHttpRequest.Builder builder = exchange.getRequest().mutate();
        mutator.accept(builder);
        return exchange.mutate().request(builder.build()).build();
    }

    private String resolveCorrelationId(ServerHttpRequest request) {
        String current = request.getHeaders().getFirst(H_CORRELATION_ID);
        return hasText(current) ? current : UUID.randomUUID().toString();
    }

    private boolean hasText(String value) {
        return value != null && !value.isBlank();
    }
}
