package com.agri.decision.service;

import com.agri.decision.client.IntegrationClient;
import com.agri.decision.client.MlClient;
import com.agri.decision.dto.DecisionRequest;
import com.agri.decision.dto.DecisionResponse;
import com.agri.decision.dto.ExternalSignalResponse;
import com.agri.decision.dto.PredictRequest;
import com.agri.decision.dto.PredictResponse;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class DecisionEngineService {

    private final MlClient mlClient;
    private final IntegrationClient integrationClient;

    public DecisionEngineService(MlClient mlClient, IntegrationClient integrationClient) {
        this.mlClient = mlClient;
        this.integrationClient = integrationClient;
    }

    public DecisionResponse analyze(DecisionRequest request) {
        PredictRequest predictRequest = new PredictRequest(
                request.country(),
                request.crop(),
                request.year(),
                request.rainMmPerYear(),
                request.pesticidesTonnes(),
                request.avgTemp()
        );

        PredictResponse prediction = mlClient.predict(predictRequest);
        ExternalSignalResponse signals = integrationClient.fetchSignals(request.country(), request.crop());

        String riskLevel = computeRiskLevel(signals);
        List<String> recommendations = buildRecommendations(riskLevel, signals);

        return new DecisionResponse(
                request.country(),
                request.crop(),
                request.year(),
                prediction.predicted_yield(),
                signals.weatherRiskScore(),
                signals.marketPriceIndex(),
                signals.ndviIndex(),
                riskLevel,
                recommendations
        );
    }

    private String computeRiskLevel(ExternalSignalResponse signal) {
        double score = (signal.weatherRiskScore() * 0.5)
                + ((1.2 - signal.marketPriceIndex()) * 0.25)
                + ((0.8 - signal.ndviIndex()) * 0.25);

        if (score >= 0.65) {
            return "HIGH";
        }
        if (score >= 0.40) {
            return "MEDIUM";
        }
        return "LOW";
    }

    private List<String> buildRecommendations(String riskLevel, ExternalSignalResponse signal) {
        List<String> recommendations = new ArrayList<>();

        if ("HIGH".equals(riskLevel)) {
            recommendations.add("Activer un plan d'irrigation prioritaire sur les parcelles critiques.");
            recommendations.add("Réduire l'exposition au risque marché via stockage et contractualisation courte.");
            recommendations.add("Déployer une alerte hebdomadaire aux décideurs régionaux.");
        } else if ("MEDIUM".equals(riskLevel)) {
            recommendations.add("Ajuster les intrants et intensifier le suivi météo terrain.");
            recommendations.add("Surveiller les prix de marché et lisser les ventes sur plusieurs semaines.");
        } else {
            recommendations.add("Maintenir la stratégie de production actuelle avec contrôle mensuel.");
        }

        if (signal.ndviIndex() < 0.45) {
            recommendations.add("NDVI faible: contrôler la vigueur végétale et cibler les apports hydriques.");
        }

        return recommendations;
    }
}
