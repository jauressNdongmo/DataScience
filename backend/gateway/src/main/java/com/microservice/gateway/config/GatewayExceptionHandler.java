package com.microservice.gateway.config;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.bind.support.WebExchangeBindException;
import org.springframework.web.server.ServerWebExchange;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

@RestControllerAdvice
public class GatewayExceptionHandler {

    @ExceptionHandler(WebExchangeBindException.class)
    public ResponseEntity<GatewayErrorPayload> handleValidation(
            WebExchangeBindException ex,
            ServerWebExchange exchange
    ) {
        Map<String, Object> fields = new HashMap<>();
        for (FieldError fieldError : ex.getBindingResult().getFieldErrors()) {
            fields.put(fieldError.getField(), fieldError.getDefaultMessage());
        }
        return build(
                exchange,
                HttpStatus.BAD_REQUEST,
                "VALIDATION_ERROR",
                "Le payload est invalide.",
                Map.of("fields", fields, "timestamp", Instant.now().toString())
        );
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<GatewayErrorPayload> handleBusiness(
            IllegalArgumentException ex,
            ServerWebExchange exchange
    ) {
        return build(
                exchange,
                HttpStatus.BAD_REQUEST,
                "BUSINESS_ERROR",
                ex.getMessage(),
                Map.of("timestamp", Instant.now().toString())
        );
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<GatewayErrorPayload> handleUnhandled(Exception ex, ServerWebExchange exchange) {
        return build(
                exchange,
                HttpStatus.INTERNAL_SERVER_ERROR,
                "INTERNAL_ERROR",
                "Une erreur interne est survenue.",
                Map.of("timestamp", Instant.now().toString())
        );
    }

    private ResponseEntity<GatewayErrorPayload> build(
            ServerWebExchange exchange,
            HttpStatus status,
            String code,
            String message,
            Map<String, Object> details
    ) {
        String correlationId = exchange.getRequest().getHeaders().getFirst("X-Correlation-Id");
        return ResponseEntity.status(status).body(new GatewayErrorPayload(code, message, details, correlationId));
    }
}
