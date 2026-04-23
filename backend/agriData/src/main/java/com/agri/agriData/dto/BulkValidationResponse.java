package com.agri.agriData.dto;

import java.util.List;

public record BulkValidationResponse(
        int totalRows,
        int validRows,
        int invalidRows,
        boolean valid,
        List<ValidationIssue> issues
) {
}
