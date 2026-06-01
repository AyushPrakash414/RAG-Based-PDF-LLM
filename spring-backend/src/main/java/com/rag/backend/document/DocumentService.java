package com.rag.backend.document;

import com.rag.backend.client.PythonRagClient;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class DocumentService {

    private final DocumentRepository documentRepository;
    private final PythonRagClient pythonRagClient;

    public DocumentEntity uploadDocument(MultipartFile file, String userId) {
        String qdrantDocId = UUID.randomUUID().toString();
        
        // Forward to Python Service
        Map response = pythonRagClient.ingestDocument(file, qdrantDocId).block(); // Blocking for simplicity in MVC controller

        DocumentEntity doc = new DocumentEntity();
        doc.setUserId(userId);
        doc.setFileName(file.getOriginalFilename());
        doc.setDocumentType(file.getContentType());
        doc.setQdrantDocumentId(qdrantDocId);
        doc.setUploadedAt(Instant.now());

        return documentRepository.save(doc);
    }

    public List<DocumentEntity> getUserDocuments(String userId) {
        return documentRepository.findByUserId(userId);
    }

    public DocumentEntity getDocumentByIdAndUserId(String id, String userId) {
        return documentRepository.findByIdAndUserId(id, userId)
                .orElseThrow(() -> new RuntimeException("Document not found or unauthorized"));
    }

    public void deleteDocument(String id, String userId) {
        DocumentEntity doc = getDocumentByIdAndUserId(id, userId);

        // Delete from Python service/Qdrant
        pythonRagClient.deleteDocument(doc.getQdrantDocumentId()).block();

        // Delete from Mongo
        documentRepository.delete(doc);
    }
}
