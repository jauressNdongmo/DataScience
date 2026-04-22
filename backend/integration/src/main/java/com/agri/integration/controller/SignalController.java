package com.agri.integration.controller;

import com.agri.integration.dto.RealtimeSignalResponse;
import com.agri.integration.service.StubExternalSignalService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/signals")
public class SignalController {

    private final StubExternalSignalService signalService;

    public SignalController(StubExternalSignalService signalService) {
        this.signalService = signalService;
    }

    @GetMapping("/realtime")
    public RealtimeSignalResponse realtime(
            @RequestParam String country,
            @RequestParam String crop
    ) {
        double weatherRisk = signalService.computeWeatherRisk(country, crop);
        double marketIndex = signalService.computeMarketIndex(country, crop);
        double ndvi = signalService.computeNdvi(country, crop);
        return new RealtimeSignalResponse(country, crop, weatherRisk, marketIndex, ndvi);
    }
}
