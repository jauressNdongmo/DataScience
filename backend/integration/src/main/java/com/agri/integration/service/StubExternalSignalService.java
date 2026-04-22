package com.agri.integration.service;

import com.agri.integration.contract.MarketProviderContract;
import com.agri.integration.contract.SatelliteProviderContract;
import com.agri.integration.contract.WeatherProviderContract;
import org.springframework.stereotype.Service;

import java.util.Locale;

@Service
public class StubExternalSignalService implements WeatherProviderContract, MarketProviderContract, SatelliteProviderContract {

    @Override
    public double computeWeatherRisk(String country, String crop) {
        int hash = Math.abs((country + crop).toLowerCase(Locale.ROOT).hashCode());
        return 0.2 + (hash % 60) / 100.0;
    }

    @Override
    public double computeMarketIndex(String country, String crop) {
        int hash = Math.abs((crop + country).toLowerCase(Locale.ROOT).hashCode());
        return 0.75 + (hash % 50) / 100.0;
    }

    @Override
    public double computeNdvi(String country, String crop) {
        int hash = Math.abs((country + ":" + crop).toLowerCase(Locale.ROOT).hashCode());
        return 0.3 + (hash % 55) / 100.0;
    }
}
