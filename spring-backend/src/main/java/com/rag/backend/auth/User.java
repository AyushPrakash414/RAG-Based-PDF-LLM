package com.rag.backend.auth;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;

@Data
@Document(collection = "users")
public class User {
    @Id
    private String id;
    
    @Indexed(unique = true)
    private String googleId;
    
    @Indexed(unique = true)
    private String email;
    
    private String name;
    private String profilePicture;
    private Instant createdAt;
}
