package com.agri.integration.controller;

import com.agri.integration.dto.RealtimeSignalResponse;
import com.agri.integration.service.ExternalSignalService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/signals")
public class SignalController {

    private final ExternalSignalService signalService;

    public SignalController(ExternalSignalService signalService) {
        this.signalService = signalService;
    }

    @GetMapping("/realtime")
    public RealtimeSignalResponse realtime(
            @RequestParam String country,
            @RequestParam String crop
    ) {
        return signalService.realtime(country, crop);
    }
}
