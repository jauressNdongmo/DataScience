package com.microservice.gateway.config;

import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class LoggingFilter implements GlobalFilter, Ordered {

    private static final Logger logger = LoggerFactory.getLogger(LoggingFilter.class);

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String correlationId = exchange.getRequest().getHeaders().getFirst("X-Correlation-Id");
        String tenantId = exchange.getRequest().getHeaders().getFirst("X-Tenant-Id");
        String userId = exchange.getRequest().getHeaders().getFirst("X-User-Id");
        logger.info(
                "Gateway request path={} correlationId={} tenantId={} userId={}",
                exchange.getRequest().getPath(),
                correlationId,
                tenantId,
                userId
        );
        return chain.filter(exchange);
    }

    @Override
    public int getOrder() {
        return -850;
    }
}
