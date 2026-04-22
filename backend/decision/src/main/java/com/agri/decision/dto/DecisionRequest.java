package com.agri.decision.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record DecisionRequest(
        @NotBlank String country,
        @NotBlank String crop,
        @NotNull @Min(1960) @Max(2100) Integer year,
        @NotNull Double rainMmPerYear,
        @NotNull Double pesticidesTonnes,
        @NotNull Double avgTemp
) {
}
