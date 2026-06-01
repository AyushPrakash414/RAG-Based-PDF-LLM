package com.rag.backend.client.dto;

import lombok.Data;

import java.util.List;

@Data
public class RagResponseDto {
    private String answer;
    private List<String> sources;
    private Double confidence;
    private Integer attempts;
}
