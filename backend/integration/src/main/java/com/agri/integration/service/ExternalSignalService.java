package com.agri.integration.service;

import com.agri.integration.config.IntegrationSignalProperties;
import com.agri.integration.contract.MarketProviderContract;
import com.agri.integration.contract.SatelliteProviderContract;
import com.agri.integration.contract.WeatherProviderContract;
import com.agri.integration.dto.RealtimeSignalResponse;
import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class ExternalSignalService implements WeatherProviderContract, MarketProviderContract, SatelliteProviderContract {

    private final RestClient restClient;
    private final IntegrationSignalProperties properties;
    private final ConcurrentHashMap<String, CacheItem> cache = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, ProviderValue> lastValidSignals = new ConcurrentHashMap<>();

    private static final Map<String, GeoPoint> COUNTRY_COORDS = Map.ofEntries(
            Map.entry("cameroon", new GeoPoint(5.9631, 12.3186, "CM")),
            Map.entry("albania", new GeoPoint(41.1533, 20.1683, "AL")),
            Map.entry("france", new GeoPoint(46.2276, 2.2137, "FR")),
            Map.entry("senegal", new GeoPoint(14.4974, -14.4524, "SN")),
            Map.entry("nigeria", new GeoPoint(9.0820, 8.6753, "NG")),
            Map.entry("ghana", new GeoPoint(7.9465, -1.0232, "GH")),
            Map.entry("kenya", new GeoPoint(-0.0236, 37.9062, "KE")),
            Map.entry("india", new GeoPoint(20.5937, 78.9629, "IN")),
            Map.entry("brazil", new GeoPoint(-14.2350, -51.9253, "BR")),
            Map.entry("usa", new GeoPoint(37.0902, -95.7129, "US")),
            Map.entry("united states", new GeoPoint(37.0902, -95.7129, "US"))
    );

    public ExternalSignalService(RestClient restClient, IntegrationSignalProperties properties) {
        this.restClient = restClient;
        this.properties = properties;
    }

    public RealtimeSignalResponse realtime(String country, String crop) {
        String key = cacheKey(country, crop);
        CacheItem cached = cache.get(key);
        if (cached != null && !isExpired(cached.createdAt)) {
            return withFreshness(cached.response, cached.createdAt);
        }

        List<String> warnings = new ArrayList<>();
        Map<String, String> sources = new HashMap<>();
        ProviderValue weather = weatherValue(country, crop);
        ProviderValue market = marketValue(country, crop);
        ProviderValue ndvi = ndviValue(country, crop);

        sources.put("weather", weather.source());
        sources.put("market", market.source());
        sources.put("ndvi", ndvi.source());
        if (weather.warning() != null) {
            warnings.add(weather.warning());
        }
        if (market.warning() != null) {
            warnings.add(market.warning());
        }
        if (ndvi.warning() != null) {
            warnings.add(ndvi.warning());
        }

        boolean degraded = weather.degraded() || market.degraded() || ndvi.degraded();
        double confidence = computeConfidence(degraded, warnings.size());
        Instant now = Instant.now();
        RealtimeSignalResponse response = new RealtimeSignalResponse(
                country,
                crop,
                weather.value(),
                market.value(),
                ndvi.value(),
                now.toString(),
                0L,
                degraded,
                confidence,
                sources,
                warnings
        );
        cache.put(key, new CacheItem(now, response));
        return response;
    }

    @Override
    public double computeWeatherRisk(String country, String crop) {
        return weatherValue(country, crop).value();
    }

    @Override
    public double computeMarketIndex(String country, String crop) {
        return marketValue(country, crop).value();
    }

    @Override
    public double computeNdvi(String country, String crop) {
        return ndviValue(country, crop).value();
    }

    private ProviderValue weatherValue(String country, String crop) {
        if (!properties.isWeatherExternalEnabled()) {
            return fallbackWeather(country, crop, "weather external disabled");
        }

        try {
            GeoPoint geo = resolveGeo(country, crop);
            String uri = properties.getWeatherApiBaseUrl()
                    + "?latitude=%s&longitude=%s&daily=temperature_2m_max,precipitation_sum&forecast_days=1&timezone=UTC"
                    .formatted(geo.latitude(), geo.longitude());
            JsonNode response = restClient.get().uri(uri).retrieve().body(JsonNode.class);
            JsonNode daily = response.path("daily");
            double temp = daily.path("temperature_2m_max").path(0).asDouble(Double.NaN);
            double rain = daily.path("precipitation_sum").path(0).asDouble(Double.NaN);
            if (Double.isNaN(temp) || Double.isNaN(rain)) {
                return fallbackWeather(country, crop, "weather API payload incomplet");
            }
            double heatStress = clamp((temp - 30.0) / 18.0, 0.0, 1.0);
            double droughtStress = clamp((40.0 - rain) / 40.0, 0.0, 1.0);
            double risk = clamp(0.15 + (0.55 * heatStress) + (0.45 * droughtStress), 0.0, 1.0);
            ProviderValue value = new ProviderValue(risk, "open-meteo", false, null);
            lastValidSignals.put(providerKey("weather", country, crop), value);
            return value;
        } catch (Exception ex) {
            return fallbackWeather(country, crop, "weather API indisponible");
        }
    }

    private ProviderValue marketValue(String country, String crop) {
        if (!properties.isMarketExternalEnabled()) {
            return fallbackMarket(country, crop, "market external disabled");
        }

        try {
            GeoPoint geo = resolveGeo(country, crop);
            String uri = properties.getMarketApiBaseUrl()
                    + "/%s/indicator/FP.CPI.TOTL?format=json&per_page=1"
                    .formatted(geo.iso2());
            JsonNode payload = restClient.get().uri(uri).retrieve().body(JsonNode.class);
            double cpi = payload.path(1).path(0).path("value").asDouble(Double.NaN);
            if (Double.isNaN(cpi) || cpi <= 0) {
                return fallbackMarket(country, crop, "market API payload incomplet");
            }
            double normalized = clamp(0.80 + (Math.log10(cpi + 1) * 0.18), 0.70, 1.30);
            ProviderValue value = new ProviderValue(normalized, "worldbank-cpi", false, null);
            lastValidSignals.put(providerKey("market", country, crop), value);
            return value;
        } catch (Exception ex) {
            return fallbackMarket(country, crop, "market API indisponible");
        }
    }

    private ProviderValue ndviValue(String country, String crop) {
        if (!properties.isNdviExternalEnabled()) {
            return fallbackNdvi(country, crop, "ndvi external disabled");
        }

        try {
            GeoPoint geo = resolveGeo(country, crop);
            String uri = properties.getWeatherApiBaseUrl()
                    + "?latitude=%s&longitude=%s&hourly=soil_moisture_0_to_1cm&forecast_days=1&timezone=UTC"
                    .formatted(geo.latitude(), geo.longitude());
            JsonNode payload = restClient.get().uri(uri).retrieve().body(JsonNode.class);
            double soilMoisture = payload.path("hourly").path("soil_moisture_0_to_1cm").path(0).asDouble(Double.NaN);
            if (Double.isNaN(soilMoisture)) {
                return fallbackNdvi(country, crop, "ndvi payload incomplet");
            }
            double ndviProxy = clamp(0.25 + (soilMoisture * 1.25), 0.20, 0.92);
            ProviderValue value = new ProviderValue(ndviProxy, "open-meteo-soil-proxy", false, null);
            lastValidSignals.put(providerKey("ndvi", country, crop), value);
            return value;
        } catch (Exception ex) {
            return fallbackNdvi(country, crop, "ndvi API indisponible");
        }
    }

    private ProviderValue fallbackWeather(String country, String crop, String reason) {
        ProviderValue lastValid = lastValidSignals.get(providerKey("weather", country, crop));
        if (lastValid != null) {
            return new ProviderValue(
                    lastValid.value(),
                    "cached-last-valid-weather",
                    true,
                    reason + " (derniere valeur valide reutilisee)"
            );
        }
        int hash = Math.abs((country + crop).toLowerCase(Locale.ROOT).hashCode());
        double value = 0.2 + (hash % 60) / 100.0;
        return new ProviderValue(value, "fallback-hash-weather", true, reason);
    }

    private ProviderValue fallbackMarket(String country, String crop, String reason) {
        ProviderValue lastValid = lastValidSignals.get(providerKey("market", country, crop));
        if (lastValid != null) {
            return new ProviderValue(
                    lastValid.value(),
                    "cached-last-valid-market",
                    true,
                    reason + " (derniere valeur valide reutilisee)"
            );
        }
        int hash = Math.abs((crop + country).toLowerCase(Locale.ROOT).hashCode());
        double value = 0.75 + (hash % 50) / 100.0;
        return new ProviderValue(value, "fallback-hash-market", true, reason);
    }

    private ProviderValue fallbackNdvi(String country, String crop, String reason) {
        ProviderValue lastValid = lastValidSignals.get(providerKey("ndvi", country, crop));
        if (lastValid != null) {
            return new ProviderValue(
                    lastValid.value(),
                    "cached-last-valid-ndvi",
                    true,
                    reason + " (derniere valeur valide reutilisee)"
            );
        }
        int hash = Math.abs((country + ":" + crop).toLowerCase(Locale.ROOT).hashCode());
        double value = 0.3 + (hash % 55) / 100.0;
        return new ProviderValue(value, "fallback-hash-ndvi", true, reason);
    }

    private RealtimeSignalResponse withFreshness(RealtimeSignalResponse payload, Instant createdAt) {
        long freshnessSeconds = Duration.between(createdAt, Instant.now()).getSeconds();
        return new RealtimeSignalResponse(
                payload.country(),
                payload.crop(),
                payload.weatherRiskScore(),
                payload.marketPriceIndex(),
                payload.ndviIndex(),
                payload.generatedAt(),
                Math.max(0, freshnessSeconds),
                payload.degraded(),
                payload.confidence(),
                payload.sources(),
                payload.warnings()
        );
    }

    private boolean isExpired(Instant createdAt) {
        return Duration.between(createdAt, Instant.now()).toSeconds() > properties.getCacheTtlSeconds();
    }

    private double computeConfidence(boolean degraded, int warningCount) {
        double score = degraded ? 0.78 : 0.94;
        score -= warningCount * 0.03;
        return clamp(score, 0.45, 0.98);
    }

    private String cacheKey(String country, String crop) {
        return normalize(country) + "|" + normalize(crop);
    }

    private String providerKey(String provider, String country, String crop) {
        return provider + "|" + cacheKey(country, crop);
    }

    private GeoPoint resolveGeo(String country, String crop) {
        String key = normalize(country);
        GeoPoint known = COUNTRY_COORDS.get(key);
        if (known != null) {
            return known;
        }
        int hash = Math.abs((country + "|" + crop).toLowerCase(Locale.ROOT).hashCode());
        double lat = -50 + (hash % 10000) * 0.01;
        double lon = -170 + (hash % 34000) * 0.01;
        return new GeoPoint(clamp(lat, -55, 70), clamp(lon, -170, 170), "US");
    }

    private String normalize(String value) {
        return value == null ? "" : value.trim().toLowerCase(Locale.ROOT);
    }

    private double clamp(double value, double min, double max) {
        return Math.max(min, Math.min(max, value));
    }

    private record ProviderValue(double value, String source, boolean degraded, String warning) {}
    private record CacheItem(Instant createdAt, RealtimeSignalResponse response) {}
    private record GeoPoint(double latitude, double longitude, String iso2) {}
}
