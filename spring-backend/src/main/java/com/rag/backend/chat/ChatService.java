package com.rag.backend.chat;

import com.rag.backend.client.PythonRagClient;
import com.rag.backend.client.dto.RagResponseDto;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ChatService {

    private final ChatSessionRepository chatSessionRepository;
    private final ChatMessageRepository chatMessageRepository;
    private final PythonRagClient pythonRagClient;
    private final com.rag.backend.document.DocumentRepository documentRepository;

    public ChatSession createSession(String userId, String title) {
        ChatSession session = new ChatSession();
        session.setUserId(userId);
        session.setTitle(title != null ? title : "New Chat");
        session.setCreatedAt(Instant.now());
        return chatSessionRepository.save(session);
    }

    public List<ChatSession> getUserSessions(String userId) {
        return chatSessionRepository.findByUserId(userId);
    }

    public ChatSession getSession(String id, String userId) {
        return chatSessionRepository.findByIdAndUserId(id, userId)
                .orElseThrow(() -> new RuntimeException("Session not found or unauthorized"));
    }

    public void deleteSession(String id, String userId) {
        ChatSession session = getSession(id, userId);
        chatMessageRepository.deleteBySessionId(session.getId());
        chatSessionRepository.delete(session);
    }

    public List<ChatMessage> getChatHistory(String sessionId, String userId) {
        // verify ownership
        getSession(sessionId, userId);
        return chatMessageRepository.findBySessionIdOrderByTimestampAsc(sessionId);
    }

    public ChatMessage askQuestion(String sessionId, String question, String userId) {
        // verify ownership
        ChatSession session = getSession(sessionId, userId);

        // Auto-generate title on first message
        if (session.getTitle().equals("New Chat") || session.getTitle().equals("New Conversation")) {
            String[] words = question.trim().split("\\s+");
            int limit = Math.min(words.length, 4);
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < limit; i++) {
                sb.append(words[i]).append(" ");
            }
            session.setTitle(sb.toString().trim() + (words.length > 4 ? "..." : ""));
            chatSessionRepository.save(session);
        }

        // Fetch allowed documents for tenant isolation
        List<String> allowedDocumentIds = documentRepository.findByUserId(userId)
                .stream()
                .map(com.rag.backend.document.DocumentEntity::getQdrantDocumentId)
                .toList();

        // Save User Message
        ChatMessage userMsg = new ChatMessage();
        userMsg.setSessionId(sessionId);
        userMsg.setRole("USER");
        userMsg.setContent(question);
        userMsg.setTimestamp(Instant.now());
        chatMessageRepository.save(userMsg);

        // Call Python Service with tenant isolation
        RagResponseDto responseDto = pythonRagClient.askQuestion(question, allowedDocumentIds).block();

        // Save AI Message
        ChatMessage aiMsg = new ChatMessage();
        aiMsg.setSessionId(sessionId);
        aiMsg.setRole("AI");
        if (responseDto != null) {
            aiMsg.setContent(responseDto.getAnswer());
            aiMsg.setSources(responseDto.getSources());
            aiMsg.setConfidence(responseDto.getConfidence());
            aiMsg.setAttempts(responseDto.getAttempts());
            aiMsg.setStatus(responseDto.getStatus());
        } else {
            aiMsg.setContent("Failed to get answer");
            aiMsg.setStatus("ERROR");
        }
        aiMsg.setTimestamp(Instant.now());
        return chatMessageRepository.save(aiMsg);
    }
}
