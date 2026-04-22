package com.agri.agriData.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record YieldRecordRequest(
        @NotBlank String country,
        @NotBlank String crop,
        @NotNull @Min(1960) @Max(2100) Integer year,
        @NotNull Double rainMmPerYear,
        @NotNull Double pesticidesTonnes,
        @NotNull Double avgTemp,
        @NotNull Double yieldValue
) {
}
