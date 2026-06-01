package com.rag.backend.chat;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;
import java.util.List;

@Data
@Document(collection = "chat_messages")
public class ChatMessage {
    @Id
    private String id;
    private String sessionId;
    private String role; // "USER" or "AI"
    private String content;
    private List<String> sources; // For AI responses
    private Instant timestamp;
}
