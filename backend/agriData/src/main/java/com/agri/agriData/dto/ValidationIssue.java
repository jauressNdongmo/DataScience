package com.agri.agriData.dto;

public record ValidationIssue(
        int rowIndex,
        String field,
        String message
) {
}
