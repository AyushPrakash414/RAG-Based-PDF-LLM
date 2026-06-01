package com.rag.backend.auth;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

@Data
@Document(collection = "avatars")
public class Avatar {
    @Id
    private String id;
    private String contentType;
    private byte[] data;
}
