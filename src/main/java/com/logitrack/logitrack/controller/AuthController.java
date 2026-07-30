package com.logitrack.logitrack.controller;

import com.logitrack.logitrack.dto.AuthRequestDTO;
import com.logitrack.logitrack.dto.AuthResponseDTO;
import com.logitrack.logitrack.util.JwtUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auth")
public class AuthController {

    private final JwtUtil jwtUtil;

    @Autowired
    public AuthController(JwtUtil jwtUtil) {
        this.jwtUtil = jwtUtil;
    }

    @PostMapping("/login")
    public AuthResponseDTO login(@RequestBody AuthRequestDTO authRequest) {

        //Por ahora, usamos credenciales fijas para simplificar
        // En una versión real, verificaríamos contra la base de datos
        String username = authRequest.getUsername();
        String password = authRequest.getPassword();

        // Credenciales de ejemplo (solo para desarrollo)
        if ("admin".equals(username) && "admin123".equals(password)) {
            String token = jwtUtil.generateToken(username, "ADMIN");
            return new AuthResponseDTO(token, username, "ADMIN");
        } else if ("user".equals(username) && "user123".equals(password)) {
            String token = jwtUtil.generateToken(username, "USER");
            return new AuthResponseDTO(token, username, "USER");
        } else {
            throw new RuntimeException("Credenciales inválidas");
        }
    }
}