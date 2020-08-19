Feature: Type registry

    Scenario: Type is added to the registry
        Given TestModel model exists
        And TestModelSerializer serializer exists for TestModel model
        And TestModelType type exists for TestModelSerializer serializer
        When TestModelType type is added to the registry
        Then TestModelType type exists in the registry for TestModel model
