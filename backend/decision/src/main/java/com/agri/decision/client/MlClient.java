package com.agri.decision.client;

import com.agri.decision.dto.PredictRequest;
import com.agri.decision.dto.PredictResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

@Component
public class MlClient {

    private final RestClient restClient;

    @Value("${app.ml.base-url}")
    private String mlBaseUrl;

    public MlClient(RestClient restClient) {
        this.restClient = restClient;
    }

    public PredictResponse predict(PredictRequest request) {
        RestClient.RequestBodySpec spec = restClient.post()
                .uri(mlBaseUrl + "/predict");
        propagateHeaders(spec);
        return spec.body(request).retrieve().body(PredictResponse.class);
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
