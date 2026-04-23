package com.agri.decision.client;

import com.agri.decision.dto.ExternalSignalResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

@Component
public class IntegrationClient {

    private final RestClient restClient;

    @Value("${app.integration.base-url}")
    private String integrationBaseUrl;

    public IntegrationClient(RestClient restClient) {
        this.restClient = restClient;
    }

    public ExternalSignalResponse fetchSignals(String country, String crop) {
        RestClient.RequestHeadersSpec<?> spec = restClient.get()
                .uri(integrationBaseUrl + "/signals/realtime?country={country}&crop={crop}", country, crop);
        propagateHeaders(spec);
        return spec.retrieve().body(ExternalSignalResponse.class);
    }

    private void propagateHeaders(RestClient.RequestHeadersSpec<?> spec) {
        ServletRequestAttributes attrs = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
        if (attrs == null) {
            return;
        }
        String[] headerNames = {"X-Correlation-Id", "X-Tenant-Id", "X-User-Id"};
        for (String name : headerNames) {
            String value = attrs.getRequest().getHeader(name);
            if (value != null && !value.isBlank()) {
                spec.header(name, value);
            }
        }
    }
}
