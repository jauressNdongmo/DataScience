package com.agri.decision.client;

import com.agri.decision.dto.PredictRequest;
import com.agri.decision.dto.PredictResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component
public class MlClient {

    private final RestClient restClient;

    @Value("${app.ml.base-url}")
    private String mlBaseUrl;

    public MlClient(RestClient restClient) {
        this.restClient = restClient;
    }

    public PredictResponse predict(PredictRequest request) {
        return restClient.post()
                .uri(mlBaseUrl + "/predict")
                .body(request)
                .retrieve()
                .body(PredictResponse.class);
    }
}
