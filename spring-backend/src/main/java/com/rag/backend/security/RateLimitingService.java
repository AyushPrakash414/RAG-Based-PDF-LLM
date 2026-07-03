package com.rag.backend.security;

import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.Bucket;
import io.github.bucket4j.BucketConfiguration;
import io.github.bucket4j.Refill;
import io.github.bucket4j.redis.lettuce.cas.LettuceBasedProxyManager;
import io.lettuce.core.RedisClient;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.function.Supplier;

@Service
@ConditionalOnProperty(name = "REDIS_URL")
public class RateLimitingService {

    private final LettuceBasedProxyManager<byte[]> proxyManager;

    public RateLimitingService(RedisClient redisClient) {
        this.proxyManager = LettuceBasedProxyManager.builderFor(redisClient)
                .withExpirationStrategy(
                        io.github.bucket4j.distributed.ExpirationAfterWriteStrategy.basedOnTimeForRefillingBucketUpToMax(Duration.ofSeconds(10))
                )
                .build();
    }

    public Bucket resolveQuestionBucket(String userId) {
        Supplier<BucketConfiguration> configSupplier = () -> {
            // 20 requests per minute
            Bandwidth limit = Bandwidth.classic(20, Refill.greedy(20, Duration.ofMinutes(1)));
            return BucketConfiguration.builder()
                    .addLimit(limit)
                    .build();
        };
        
        return proxyManager.builder().build(("rate_limit:questions:" + userId).getBytes(), configSupplier);
    }

    public Bucket resolveUploadBucket(String userId) {
        Supplier<BucketConfiguration> configSupplier = () -> {
            // 5 uploads per hour
            Bandwidth limit = Bandwidth.classic(5, Refill.greedy(5, Duration.ofHours(1)));
            return BucketConfiguration.builder()
                    .addLimit(limit)
                    .build();
        };
        
        return proxyManager.builder().build(("rate_limit:uploads:" + userId).getBytes(), configSupplier);
    }
}
