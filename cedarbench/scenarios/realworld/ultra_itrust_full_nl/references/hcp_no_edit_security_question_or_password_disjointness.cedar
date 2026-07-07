permit (principal, action == Action::"editDemographicInformation", resource is DemographicInformation) when { !(principal is HealthCareProfessional && context.includesSecurityQuestionOrPassword) };
