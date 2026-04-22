package com.agri.decision.controller;

import com.agri.decision.dto.DecisionRequest;
import com.agri.decision.dto.DecisionResponse;
import com.agri.decision.service.DecisionEngineService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/analysis")
public class DecisionController {

    private final DecisionEngineService decisionEngineService;

    public DecisionController(DecisionEngineService decisionEngineService) {
        this.decisionEngineService = decisionEngineService;
    }

    @PostMapping
    public DecisionResponse analyze(@RequestBody @Valid DecisionRequest request) {
        return decisionEngineService.analyze(request);
    }
}
