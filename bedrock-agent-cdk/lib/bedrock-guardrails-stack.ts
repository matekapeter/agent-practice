import * as cdk from 'aws-cdk-lib';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
import { Construct } from 'constructs';

export class BedrockGuardrailsStack extends cdk.Stack {
  public readonly guardrailArn: string;
  public readonly guardrailId: string;
  public readonly guardrailVersion: string;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create Bedrock Guardrail with comprehensive safety measures
    const guardrail = new bedrock.CfnGuardrail(this, 'BedrockGuardrail', {
      name: 'comprehensive-ai-guardrail',
      description: 'Comprehensive guardrail for AI agent with content filtering, PII protection, and contextual grounding',
      blockedInputMessaging: 'I apologize, but I cannot process your request as it contains content that violates our safety guidelines. Please rephrase your question in a way that complies with our content policy.',
      blockedOutputsMessaging: 'I apologize, but I cannot provide a response as it would violate our safety guidelines. Please ask a different question that I can help you with.',
      
      // Content Policy Configuration - Filters harmful content categories
      contentPolicyConfig: {
        filtersConfig: [
          {
            inputStrength: 'HIGH',
            outputStrength: 'HIGH',
            type: 'SEXUAL'
          },
          {
            inputStrength: 'HIGH',
            outputStrength: 'HIGH',
            type: 'VIOLENCE'
          },
          {
            inputStrength: 'HIGH',
            outputStrength: 'HIGH',
            type: 'HATE'
          },
          {
            inputStrength: 'HIGH',
            outputStrength: 'HIGH',
            type: 'INSULTS'
          },
          {
            inputStrength: 'HIGH',
            outputStrength: 'HIGH',
            type: 'MISCONDUCT'
          },
          {
            inputStrength: 'MEDIUM',
            outputStrength: 'MEDIUM',
            type: 'PROMPT_ATTACK'
          }
        ]
      },

      // Topic Policy Configuration - Define denied topics
      topicPolicyConfig: {
        topicsConfig: [
          {
            name: 'IllegalActivities',
            definition: 'Topics related to illegal activities, criminal behavior, or violation of laws',
            examples: [
              'How to hack into computer systems',
              'Instructions for creating illegal substances',
              'Methods to evade law enforcement',
              'Guidance on tax evasion'
            ],
            type: 'DENY'
          },
          {
            name: 'FinancialAdvice',
            definition: 'Specific investment advice, stock recommendations, or financial planning that requires professional licensing',
            examples: [
              'Which stocks should I buy today',
              'How to avoid paying taxes legally',
              'Best cryptocurrency investments',
              'Guaranteed ways to make money'
            ],
            type: 'DENY'
          },
          {
            name: 'MedicalDiagnosis',
            definition: 'Medical diagnosis, treatment recommendations, or health advice that requires medical professional consultation',
            examples: [
              'Do I have cancer based on these symptoms',
              'What medication should I take for this condition',
              'How to treat a serious injury at home',
              'Is this rash something serious'
            ],
            type: 'DENY'
          }
        ]
      },

      // Word Policy Configuration - Block specific words and phrases
      wordPolicyConfig: {
        wordsConfig: [
          { text: 'BLOCKED_WORD_1' },
          { text: 'INAPPROPRIATE_TERM' },
          { text: 'OFFENSIVE_PHRASE' }
        ],
        managedWordListsConfig: [
          { type: 'PROFANITY' }
        ]
      },

      // Sensitive Information Policy Configuration - PII and custom patterns
      sensitiveInformationPolicyConfig: {
        piiEntitiesConfig: [
          {
            action: 'BLOCK',
            type: 'EMAIL'
          },
          {
            action: 'BLOCK',
            type: 'PHONE'
          },
          {
            action: 'ANONYMIZE',
            type: 'NAME'
          },
          {
            action: 'BLOCK',
            type: 'ADDRESS'
          },
          {
            action: 'BLOCK',
            type: 'SSN'
          },
          {
            action: 'BLOCK',
            type: 'CREDIT_DEBIT_CARD_NUMBER'
          },
          {
            action: 'ANONYMIZE',
            type: 'DATE_TIME'
          },
          {
            action: 'BLOCK',
            type: 'IP_ADDRESS'
          }
        ],
        regexesConfig: [
          {
            action: 'BLOCK',
            description: 'Block employee IDs in format EMP-XXXXX',
            name: 'EmployeeID',
            pattern: 'EMP-[0-9]{5}'
          },
          {
            action: 'ANONYMIZE',
            description: 'Anonymize internal project codes',
            name: 'ProjectCode',
            pattern: 'PRJ-[A-Z]{3}-[0-9]{4}'
          }
        ]
      },

      // Contextual Grounding Checks - Detect hallucinations and ensure relevance
      contextualGroundingPolicyConfig: {
        filtersConfig: [
          {
            threshold: 0.75,
            type: 'GROUNDING'
          },
          {
            threshold: 0.8,
            type: 'RELEVANCE'
          }
        ]
      }
    });

    // Create a version of the guardrail for deployment
    const guardrailVersion = new bedrock.CfnGuardrailVersion(this, 'GuardrailVersion', {
      guardrailIdentifier: guardrail.attrGuardrailId,
      description: `Guardrail version created at ${new Date().toISOString()}`,
    });

    // Store outputs for use in other stacks
    this.guardrailArn = guardrail.attrGuardrailArn;
    this.guardrailId = guardrail.attrGuardrailId;
    this.guardrailVersion = guardrailVersion.attrVersion;

    // Export values for cross-stack references
    new cdk.CfnOutput(this, 'GuardrailArn', {
      value: this.guardrailArn,
      description: 'ARN of the Bedrock Guardrail',
      exportName: `${this.stackName}-GuardrailArn`,
    });

    new cdk.CfnOutput(this, 'GuardrailId', {
      value: this.guardrailId,
      description: 'ID of the Bedrock Guardrail',
      exportName: `${this.stackName}-GuardrailId`,
    });

    new cdk.CfnOutput(this, 'GuardrailVersion', {
      value: this.guardrailVersion,
      description: 'Version of the Bedrock Guardrail',
      exportName: `${this.stackName}-GuardrailVersion`,
    });

    // Tag resources
    cdk.Tags.of(this).add('Component', 'Guardrails');
    cdk.Tags.of(this).add('Purpose', 'AI Safety');
  }
}