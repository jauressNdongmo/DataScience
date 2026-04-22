package com.agri.decision.client;

import com.agri.decision.dto.ExternalSignalResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component
public class IntegrationClient {

    private final RestClient restClient;

    @Value("${app.integration.base-url}")
    private String integrationBaseUrl;

    public IntegrationClient(RestClient restClient) {
        this.restClient = restClient;
    }

    public ExternalSignalResponse fetchSignals(String country, String crop) {
        return restClient.get()
                .uri(integrationBaseUrl + "/signals/realtime?country={country}&crop={crop}", country, crop)
                .retrieve()
                .body(ExternalSignalResponse.class);
    }
}
