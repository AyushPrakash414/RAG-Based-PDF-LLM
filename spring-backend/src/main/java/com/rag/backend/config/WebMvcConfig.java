package com.rag.backend.config;

import com.rag.backend.security.RateLimitingInterceptor;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import java.util.Optional;

@Configuration
@RequiredArgsConstructor
public class WebMvcConfig implements WebMvcConfigurer {

    private final Optional<RateLimitingInterceptor> rateLimitingInterceptor;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        rateLimitingInterceptor.ifPresent(interceptor -> 
            registry.addInterceptor(interceptor)
                    .addPathPatterns("/chat/ask/**", "/documents/upload")
        );
    }
}
