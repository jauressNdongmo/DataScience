package com.agri.integration.config;

import jakarta.validation.constraints.Min;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

@Validated
@ConfigurationProperties(prefix = "app.integration")
public class IntegrationSignalProperties {

    @Min(30)
    private int cacheTtlSeconds = 300;

    private boolean weatherExternalEnabled = true;
    private boolean marketExternalEnabled = true;
    private boolean ndviExternalEnabled = true;

    private String weatherApiBaseUrl = "https://api.open-meteo.com/v1/forecast";
    private String marketApiBaseUrl = "https://api.worldbank.org/v2/country";

    public int getCacheTtlSeconds() {
        return cacheTtlSeconds;
    }

    public void setCacheTtlSeconds(int cacheTtlSeconds) {
        this.cacheTtlSeconds = cacheTtlSeconds;
    }

    public boolean isWeatherExternalEnabled() {
        return weatherExternalEnabled;
    }

    public void setWeatherExternalEnabled(boolean weatherExternalEnabled) {
        this.weatherExternalEnabled = weatherExternalEnabled;
    }

    public boolean isMarketExternalEnabled() {
        return marketExternalEnabled;
    }

    public void setMarketExternalEnabled(boolean marketExternalEnabled) {
        this.marketExternalEnabled = marketExternalEnabled;
    }

    public boolean isNdviExternalEnabled() {
        return ndviExternalEnabled;
    }

    public void setNdviExternalEnabled(boolean ndviExternalEnabled) {
        this.ndviExternalEnabled = ndviExternalEnabled;
    }

    public String getWeatherApiBaseUrl() {
        return weatherApiBaseUrl;
    }

    public void setWeatherApiBaseUrl(String weatherApiBaseUrl) {
        this.weatherApiBaseUrl = weatherApiBaseUrl;
    }

    public String getMarketApiBaseUrl() {
        return marketApiBaseUrl;
    }

    public void setMarketApiBaseUrl(String marketApiBaseUrl) {
        this.marketApiBaseUrl = marketApiBaseUrl;
    }
}
