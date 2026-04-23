package com.agri.decision.config;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

@Validated
@ConfigurationProperties(prefix = "app.decision")
public class DecisionRiskProperties {

    @DecimalMin("0.0")
    @DecimalMax("1.0")
    private double weatherWeight = 0.50;

    @DecimalMin("0.0")
    @DecimalMax("1.0")
    private double marketWeight = 0.25;

    @DecimalMin("0.0")
    @DecimalMax("1.0")
    private double ndviWeight = 0.25;

    @DecimalMin("0.0")
    @DecimalMax("1.0")
    private double highThreshold = 0.65;

    @DecimalMin("0.0")
    @DecimalMax("1.0")
    private double mediumThreshold = 0.40;

    public double getWeatherWeight() {
        return weatherWeight;
    }

    public void setWeatherWeight(double weatherWeight) {
        this.weatherWeight = weatherWeight;
    }

    public double getMarketWeight() {
        return marketWeight;
    }

    public void setMarketWeight(double marketWeight) {
        this.marketWeight = marketWeight;
    }

    public double getNdviWeight() {
        return ndviWeight;
    }

    public void setNdviWeight(double ndviWeight) {
        this.ndviWeight = ndviWeight;
    }

    public double getHighThreshold() {
        return highThreshold;
    }

    public void setHighThreshold(double highThreshold) {
        this.highThreshold = highThreshold;
    }

    public double getMediumThreshold() {
        return mediumThreshold;
    }

    public void setMediumThreshold(double mediumThreshold) {
        this.mediumThreshold = mediumThreshold;
    }
}
