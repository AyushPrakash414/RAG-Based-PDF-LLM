package com.rag.backend.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class WebClientConfig {

    @Value("${python.service.url}")
    private String pythonServiceUrl;

    @Value("${internal.api.secret:}")
    private String internalApiSecret;

    @Bean
    public WebClient pythonServiceClient() {
        WebClient.Builder builder = WebClient.builder()
                .baseUrl(pythonServiceUrl);

        // Add HMAC signing filter if secret is configured
        if (internalApiSecret != null && !internalApiSecret.isBlank()) {
            builder.filter(new HmacSigningFilter(internalApiSecret));
        }

        return builder.build();
    }
}
