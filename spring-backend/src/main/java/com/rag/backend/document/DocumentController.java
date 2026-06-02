package com.rag.backend.document;

import com.rag.backend.security.UserPrincipal;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/documents")
@RequiredArgsConstructor
public class DocumentController {

    private final DocumentService documentService;

    @PostMapping("/upload")
    public ResponseEntity<?> uploadDocument(@RequestParam("file") MultipartFile file, 
                                            @AuthenticationPrincipal UserPrincipal userPrincipal) {
        try {
            DocumentEntity savedDoc = documentService.uploadDocument(file, userPrincipal.getId());
            return ResponseEntity.ok(savedDoc);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body("Failed to upload document: " + e.getMessage());
        }
    }

    @GetMapping
    public ResponseEntity<?> getDocuments(@AuthenticationPrincipal UserPrincipal userPrincipal) {
        return ResponseEntity.ok(documentService.getUserDocuments(userPrincipal.getId()));
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> getDocument(@PathVariable String id, @AuthenticationPrincipal UserPrincipal userPrincipal) {
        try {
            return ResponseEntity.ok(documentService.getDocumentByIdAndUserId(id, userPrincipal.getId()));
        } catch (Exception e) {
            return ResponseEntity.status(404).body(e.getMessage());
        }
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteDocument(@PathVariable String id, @AuthenticationPrincipal UserPrincipal userPrincipal) {
        try {
            documentService.deleteDocument(id, userPrincipal.getId());
            return ResponseEntity.ok("Document deleted successfully");
        } catch (Exception e) {
            return ResponseEntity.status(500).body("Error deleting document: " + e.getMessage());
        }
    }
}
