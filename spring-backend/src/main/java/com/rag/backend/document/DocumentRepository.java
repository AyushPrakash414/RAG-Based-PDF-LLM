package com.rag.backend.document;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;
import java.util.Optional;

public interface DocumentRepository extends MongoRepository<DocumentEntity, String> {
    List<DocumentEntity> findByUserId(String userId);
    Optional<DocumentEntity> findByIdAndUserId(String id, String userId);
}
