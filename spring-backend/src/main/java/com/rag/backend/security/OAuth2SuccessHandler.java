package com.rag.backend.security;

import com.rag.backend.auth.RefreshToken;
import com.rag.backend.auth.RefreshTokenService;
import com.rag.backend.auth.User;
import com.rag.backend.auth.UserService;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationSuccessHandler;
import org.springframework.stereotype.Component;

import java.io.IOException;

@Component
@RequiredArgsConstructor
public class OAuth2SuccessHandler extends SimpleUrlAuthenticationSuccessHandler {

    private final JwtUtils jwtUtils;
    private final UserService userService;
    private final RefreshTokenService refreshTokenService;

    @Value("${cors.allowed-origins}")
    private String frontendUrl;

    @Override
    public void onAuthenticationSuccess(HttpServletRequest request, HttpServletResponse response, Authentication authentication) throws IOException, ServletException {
        OAuth2User oAuth2User = (OAuth2User) authentication.getPrincipal();
        String email = oAuth2User.getAttribute("email");
        String name = oAuth2User.getAttribute("name");
        String picture = oAuth2User.getAttribute("picture");
        String googleId = oAuth2User.getAttribute("sub");

        User user = userService.processOAuthPostLogin(email, googleId, name, picture);

        String jwt = jwtUtils.generateTokenFromUserId(user.getId());
        RefreshToken refreshToken = refreshTokenService.createRefreshToken(user.getId());

        // Add refresh token to HttpOnly cookie
        Cookie refreshTokenCookie = new Cookie("refresh_token", refreshToken.getToken());
        refreshTokenCookie.setHttpOnly(true);
        refreshTokenCookie.setSecure(true); // Should be true in production (HTTPS)
        refreshTokenCookie.setPath("/");
        refreshTokenCookie.setMaxAge(8 * 24 * 60 * 60); // 8 days
        response.addCookie(refreshTokenCookie);

        // Redirect to frontend with access token
        getRedirectStrategy().sendRedirect(request, response, frontendUrl + "/oauth2/redirect?token=" + jwt);
    }
}
