Feature: Works as a Pytest plugin

  Background: Tests
    Given We have tests

  Scenario: We run pytest
    When we run pytest
    Then features should be collected
    Then steps are collected

  Scenario: We run pytest specifying a feature directory
    When we run pytest with a feature directory
    Then steps are collected

