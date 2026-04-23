package com.agri.decision.service;

import com.agri.decision.client.IntegrationClient;
import com.agri.decision.client.MlClient;
import com.agri.decision.config.DecisionRiskProperties;
import com.agri.decision.dto.DecisionRequest;
import com.agri.decision.dto.DecisionResponse;
import com.agri.decision.dto.ExternalSignalResponse;
import com.agri.decision.dto.PredictRequest;
import com.agri.decision.dto.PredictResponse;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class DecisionEngineService {

    private final MlClient mlClient;
    private final IntegrationClient integrationClient;
    private final DecisionRiskProperties riskProperties;

    public DecisionEngineService(
            MlClient mlClient,
            IntegrationClient integrationClient,
            DecisionRiskProperties riskProperties
    ) {
        this.mlClient = mlClient;
        this.integrationClient = integrationClient;
        this.riskProperties = riskProperties;
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

        Map<String, Double> contributions = computeContributions(signals);
        double riskScore = contributions.values().stream().mapToDouble(Double::doubleValue).sum();
        String riskLevel = computeRiskLevel(riskScore);
        List<String> recommendations = buildRecommendations(riskLevel, signals, riskScore);

        double confidence = computeConfidence(signals, riskScore);
        List<String> warnings = new ArrayList<>();
        if (signals.warnings() != null) {
            warnings.addAll(signals.warnings());
        }
        if (signals.signalFreshnessSeconds() > 3600) {
            warnings.add("Les signaux externes ont plus d'une heure de fraicheur.");
        }

        return new DecisionResponse(
                request.country(),
                request.crop(),
                request.year(),
                prediction.predicted_yield(),
                prediction.model_version(),
                prediction.year_min(),
                prediction.year_max(),
                signals.weatherRiskScore(),
                signals.marketPriceIndex(),
                signals.ndviIndex(),
                riskScore,
                riskLevel,
                confidence,
                signals.degraded(),
                signals.signalFreshnessSeconds(),
                contributions,
                signals.sources(),
                warnings,
                recommendations
        );
    }

    private Map<String, Double> computeContributions(ExternalSignalResponse signal) {
        Map<String, Double> contributions = new HashMap<>();
        contributions.put("weather", signal.weatherRiskScore() * riskProperties.getWeatherWeight());
        contributions.put("market", (1.2 - signal.marketPriceIndex()) * riskProperties.getMarketWeight());
        contributions.put("ndvi", (0.8 - signal.ndviIndex()) * riskProperties.getNdviWeight());
        return contributions;
    }

    private String computeRiskLevel(double riskScore) {
        if (riskScore >= riskProperties.getHighThreshold()) {
            return "HIGH";
        }
        if (riskScore >= riskProperties.getMediumThreshold()) {
            return "MEDIUM";
        }
        return "LOW";
    }

    private double computeConfidence(ExternalSignalResponse signal, double riskScore) {
        double score = 0.55 + (signal.confidence() * 0.45);
        if (signal.degraded()) {
            score -= 0.08;
        }
        if (riskScore > 1.0) {
            score -= 0.05;
        }
        return Math.max(0.35, Math.min(0.99, score));
    }

    private List<String> buildRecommendations(String riskLevel, ExternalSignalResponse signal, double riskScore) {
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
        if (signal.degraded()) {
            recommendations.add("Mode dégradé: vérifier les fournisseurs externes avant décisions irréversibles.");
        }
        recommendations.add("Score de risque consolidé: %.3f.".formatted(riskScore));

        return recommendations;
    }
}
