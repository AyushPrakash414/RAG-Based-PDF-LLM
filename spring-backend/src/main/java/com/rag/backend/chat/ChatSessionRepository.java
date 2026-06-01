package com.rag.backend.chat;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.List;
import java.util.Optional;

public interface ChatSessionRepository extends MongoRepository<ChatSession, String> {
    List<ChatSession> findByUserId(String userId);
    Optional<ChatSession> findByIdAndUserId(String id, String userId);
}
