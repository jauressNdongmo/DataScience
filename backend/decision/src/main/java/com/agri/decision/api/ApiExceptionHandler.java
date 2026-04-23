package com.agri.decision.api;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiError> handleValidation(MethodArgumentNotValidException ex, HttpServletRequest request) {
        Map<String, Object> fields = new HashMap<>();
        for (FieldError fieldError : ex.getBindingResult().getFieldErrors()) {
            fields.put(fieldError.getField(), fieldError.getDefaultMessage());
        }
        return build(
                request,
                HttpStatus.BAD_REQUEST,
                "VALIDATION_ERROR",
                "Le payload est invalide",
                Map.of("fields", fields, "timestamp", Instant.now().toString())
        );
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ApiError> handleBusiness(IllegalArgumentException ex, HttpServletRequest request) {
        return build(
                request,
                HttpStatus.BAD_REQUEST,
                "BUSINESS_ERROR",
                ex.getMessage(),
                Map.of("timestamp", Instant.now().toString())
        );
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiError> handleUnhandled(Exception ex, HttpServletRequest request) {
        return build(
                request,
                HttpStatus.INTERNAL_SERVER_ERROR,
                "INTERNAL_ERROR",
                "Une erreur interne est survenue",
                Map.of("timestamp", Instant.now().toString())
        );
    }

    private ResponseEntity<ApiError> build(
            HttpServletRequest request,
            HttpStatus status,
            String code,
            String message,
            Map<String, Object> details
    ) {
        String correlationId = request.getHeader("X-Correlation-Id");
        return ResponseEntity.status(status).body(new ApiError(code, message, details, correlationId));
    }
}
