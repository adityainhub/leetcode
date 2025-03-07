package com.project.LcPlag.controller;

import com.project.LcPlag.model.Submissions;
import com.project.LcPlag.service.SubmissionService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/submissions")
public class SubmissionController {

    private final SubmissionService submissionService;

    public SubmissionController(SubmissionService submissionService) {
        this.submissionService = submissionService;
    }

    @GetMapping
    public List<Submissions> getAllSubmissions() {
        return submissionService.getAllSubmissions();
    }

    @PostMapping
    public void addSubmission(@RequestBody Submissions submission) {
        submissionService.saveSubmission(submission);
    }
}