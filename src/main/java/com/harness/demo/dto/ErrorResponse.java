package com.harness.demo.dto;

import java.time.Instant;
import java.util.List;
import java.util.Map;

public record ErrorResponse(
        Instant timestamp,
        int status,
        String error,
        String message,
        String path,
        String correlationId,
        Map<String, List<String>> validationErrors
) {
    public ErrorResponse(int status, String error, String message, String path, String correlationId) {
        this(Instant.now(), status, error, message, path, correlationId, null);
    }

    public ErrorResponse(int status, String error, String message, String path, String correlationId, Map<String, List<String>> validationErrors) {
        this(Instant.now(), status, error, message, path, correlationId, validationErrors);
    }
}
