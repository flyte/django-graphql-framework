Feature: Type registry

    Scenario: Type is added to the registry
        Given TestModel model exists
        And TestModelSerializer serializer exists for TestModel model
        And TestModelType type exists for TestModelSerializer serializer
        When TestModelType type is added to the registry
        Then TestModelType type exists in the registry for TestModel model

    Scenario: Type is converted to GraphQLObjectType when added to registry
        Given TestModel model exists
        And TestModelSerializer serializer exists for TestModel model
        And TestModelType type exists for TestModelSerializer serializer
        When TestModelType type is added to the registry
        Then Registry entry for TestModel model is a GraphQLObjectType

    Scenario Outline: Serializer fields are converted to GraphQL fields when added to registry
        Given TestModel model exists with a <model_field> test field
        And TestModelSerializer serializer exists for TestModel model
        And TestModelType type exists for TestModelSerializer serializer
        When TestModelType type is added to the registry
        Then Registry entry for TestModel model has test field converted to GraphQL <gql_field> field

        Examples: Field Types
            | model_field | gql_field     |
            | CharField   | GraphQLString |
