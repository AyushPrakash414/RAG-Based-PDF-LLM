package com.rag.backend.auth;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;

    public User processOAuthPostLogin(String email, String googleId, String name, String pictureUrl) {
        Optional<User> existUser = userRepository.findByEmail(email);

        if (existUser.isPresent()) {
            User user = existUser.get();
            // Update details if needed
            user.setName(name);
            user.setProfilePicture(pictureUrl);
            user.setGoogleId(googleId);
            return userRepository.save(user);
        }

        User newUser = new User();
        newUser.setEmail(email);
        newUser.setGoogleId(googleId);
        newUser.setName(name);
        newUser.setProfilePicture(pictureUrl);
        newUser.setCreatedAt(Instant.now());

        return userRepository.save(newUser);
    }

    public Optional<User> findById(String id) {
        return userRepository.findById(id);
    }
}
