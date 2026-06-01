package com.rag.backend.client;

import com.rag.backend.client.dto.RagResponseDto;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.Map;

@Component
@RequiredArgsConstructor
public class PythonRagClient {

    private final WebClient pythonServiceClient;

    public Mono<RagResponseDto> askQuestion(String question) {
        return pythonServiceClient.post()
                .uri("/ask")
                .bodyValue(Map.of("question", question))
                .retrieve()
                .bodyToMono(RagResponseDto.class);
    }

    public Mono<Map> ingestDocument(MultipartFile file, String documentId) {
        MultipartBodyBuilder builder = new MultipartBodyBuilder();
        builder.part("file", file.getResource());
        builder.part("document_id", documentId);

        return pythonServiceClient.post()
                .uri("/documents/ingest")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(BodyInserters.fromMultipartData(builder.build()))
                .retrieve()
                .bodyToMono(Map.class);
    }

    public Mono<Void> deleteDocument(String qdrantDocumentId) {
        return pythonServiceClient.delete()
                .uri("/documents/{id}", qdrantDocumentId)
                .retrieve()
                .bodyToMono(Void.class);
    }
}
