Feature: Type registry

    Scenario: Type is added to the registry
        Given TestModel model exists
        And Serializer exists for TestModel model
        And TestModelType type exists for TestModel model serializer
        When TestModelType type is added to the registry
        Then TestModelType type exists in the registry for TestModel model

    Scenario: Type is converted to GraphQLObjectType when added to registry
        Given TestModel model exists
        And Serializer exists for TestModel model
        And TestModelType type exists for TestModel model serializer
        When TestModelType type is added to the registry
        Then Registry entry for TestModel model is a GraphQLObjectType

    Scenario Outline: Serializer fields are converted to GraphQL fields when added to registry
        Given TestModel model exists with a <model_field> test field
        And Serializer exists for TestModel model
        And TestModelType type exists for TestModel model serializer
        When TestModelType type is added to the registry
        Then Registry entry for TestModel model has test field converted to GraphQL <gql_field> field

        Examples: Field Types
            | model_field  | gql_field     |
            | CharField    | GraphQLString |
            | TextField    | GraphQLString |
            | EmailField   | GraphQLString |
            | IntegerField | GraphQLInt    |
            | FloatField   | GraphQLFloat  |

    @wip
    Scenario Outline: TypedSerializerMethodField is represented by its field type
        Given TestModel model exists
        And Serializer exists for TestModel model with a <serializer_field> TypedSerializerMethodField
        And TestModelType type exists for TestModel model serializer
        When TestModelType type is added to the registry
        Then Registry entry for TestModel model has test field converted to GraphQL <gql_field> field

        Examples: Field Types
            | serializer_field | gql_field     |
            | CharField        | GraphQLString |

