package com.rag.backend.document;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

@Data
@Document(collection = "documents")
public class DocumentEntity {
    @Id
    private String id;
    private String userId;
    private String fileName;
    private String documentType;
    private String qdrantDocumentId;
    private Instant uploadedAt;
}
