package com.rag.backend.config;

import org.springframework.web.reactive.function.client.ClientRequest;
import org.springframework.web.reactive.function.client.ClientResponse;
import org.springframework.web.reactive.function.client.ExchangeFilterFunction;
import org.springframework.web.reactive.function.client.ExchangeFunction;
import reactor.core.publisher.Mono;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/**
 * WebClient filter that adds HMAC-SHA256 signature headers to every
 * outgoing request for service-to-service authentication.
 *
 * <p>Headers added:
 * <ul>
 *   <li>{@code X-Service-Timestamp} — Unix epoch seconds</li>
 *   <li>{@code X-Service-Signature} — HMAC-SHA256 hex signature</li>
 * </ul>
 *
 * <p>Signature scheme:
 * {@code HMAC-SHA256(secret, timestamp + "." + method + "." + path + "." + sha256(body))}
 */
public class HmacSigningFilter implements ExchangeFilterFunction {

    private final String secret;

    public HmacSigningFilter(String secret) {
        this.secret = secret;
    }

    @Override
    public Mono<ClientResponse> filter(ClientRequest request, ExchangeFunction next) {
        String timestamp = String.valueOf(System.currentTimeMillis() / 1000);
        String method = request.method().name().toUpperCase();
        String path = request.url().getPath();

        // For non-body requests, use empty body hash
        String bodyHash = sha256("");

        String signature = computeSignature(timestamp, method, path, bodyHash);

        ClientRequest signedRequest = ClientRequest.from(request)
                .header("X-Service-Timestamp", timestamp)
                .header("X-Service-Signature", signature)
                .build();

        return next.exchange(signedRequest);
    }

    private String computeSignature(String timestamp, String method, String path, String bodyHash) {
        String message = timestamp + "." + method + "." + path + "." + bodyHash;
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            SecretKeySpec keySpec = new SecretKeySpec(
                    secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
            mac.init(keySpec);
            byte[] rawHmac = mac.doFinal(message.getBytes(StandardCharsets.UTF_8));
            return bytesToHex(rawHmac);
        } catch (Exception e) {
            throw new RuntimeException("Failed to compute HMAC signature", e);
        }
    }

    private static String sha256(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(input.getBytes(StandardCharsets.UTF_8));
            return bytesToHex(hash);
        } catch (Exception e) {
            throw new RuntimeException("Failed to compute SHA-256", e);
        }
    }

    private static String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }
}
