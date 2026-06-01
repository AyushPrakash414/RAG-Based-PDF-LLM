package com.rag.backend.chat;

import com.rag.backend.security.UserPrincipal;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/chat")
@RequiredArgsConstructor
public class ChatController {

    private final ChatService chatService;

    @PostMapping("/session")
    public ResponseEntity<?> createSession(@RequestBody(required = false) Map<String, String> request, 
                                           @AuthenticationPrincipal UserPrincipal userPrincipal) {
        String title = request != null ? request.get("title") : null;
        return ResponseEntity.ok(chatService.createSession(userPrincipal.getId(), title));
    }

    @GetMapping("/session")
    public ResponseEntity<?> getSessions(@AuthenticationPrincipal UserPrincipal userPrincipal) {
        return ResponseEntity.ok(chatService.getUserSessions(userPrincipal.getId()));
    }

    @GetMapping("/session/{id}")
    public ResponseEntity<?> getSession(@PathVariable String id, @AuthenticationPrincipal UserPrincipal userPrincipal) {
        try {
            return ResponseEntity.ok(chatService.getSession(id, userPrincipal.getId()));
        } catch (Exception e) {
            return ResponseEntity.status(404).body(e.getMessage());
        }
    }

    @DeleteMapping("/session/{id}")
    public ResponseEntity<?> deleteSession(@PathVariable String id, @AuthenticationPrincipal UserPrincipal userPrincipal) {
        try {
            chatService.deleteSession(id, userPrincipal.getId());
            return ResponseEntity.ok("Session deleted successfully");
        } catch (Exception e) {
            return ResponseEntity.status(404).body(e.getMessage());
        }
    }

    @GetMapping("/history/{sessionId}")
    public ResponseEntity<?> getHistory(@PathVariable String sessionId, @AuthenticationPrincipal UserPrincipal userPrincipal) {
        try {
            return ResponseEntity.ok(chatService.getChatHistory(sessionId, userPrincipal.getId()));
        } catch (Exception e) {
            return ResponseEntity.status(404).body(e.getMessage());
        }
    }

    @PostMapping("/ask/{sessionId}")
    public ResponseEntity<?> askQuestion(@PathVariable String sessionId, 
                                         @RequestBody Map<String, String> request, 
                                         @AuthenticationPrincipal UserPrincipal userPrincipal) {
        try {
            String question = request.get("question");
            return ResponseEntity.ok(chatService.askQuestion(sessionId, question, userPrincipal.getId()));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Failed to get answer: " + e.getMessage());
        }
    }
}
