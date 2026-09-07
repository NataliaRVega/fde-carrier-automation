# fde-carrier-automation
*AI-Powered Inbound Carrier Sales Automation*

An AI-powered inbound carrier sales automation system for freight brokerage, combining conversational agents, deterministic business policies, carrier varification, OTP authentication, legacy TMS integration, rate negotiation, booking, and operational workflows.

## HappyRobot FDE Technical Challenge - Inbound Carrier Sales Automation

# OVERVIEW

This project implements an automated inbound carrier sales workflow for a freight brokerage environment.
The system is designed to allow carriers to interact with an AI agent that can:

1. Identify and verify the carrier
2. Validate FMCSA operating authority
3. Complete OTP verification for new or unverified carriers.
4. Search available loads based on lane and equipment.
5. Present eligible load offers.
6. Negotiate rates within predefined business constraints
7. Book the load through legacy TMS
8. Hand off completed transactions to a senior representative when required
9. Maintain an auditable record of the interaction and outcome


 The architecture intentionally separates conversational intelligence from transaction-critical business logic.

 *The intelligence is agentic, but the transaction is deterministic*

 The LLM is responsible for understanding and conducting the conversation, while deterministic services enforce compliance, authorization, negotiation and booking policies.

 ## Business Context 

 The target environment is a mid-sized freight brokerage managing approximately:
 - 2,000 active carriers
 - 500 loads per week
 - Dry van, refrigerated and flatbed equipment

The existing inbound carrier process is highly manual. Dispatchers receive carrier calls, verify credentials, search for loads, negotiate rates, and hand off transactions to senior representatives.

This creates several operational challenges:
- Missed calls and long hold times
- Inconsistent rate negotiation
- Manual FMCSA verification
- Limited auditability
- Dispatcher workload and burnout
- Limited scalability during periods of high call volume

The goal of this solution is to automate the first leg of the carrier sales process while preserving strict controls around compliance, pricing and booking

*Core workflow*

Carrier 
-> Inbound call 
-> Carrier identification 
-> (FMCSA Verification 
    -> OTP Verification 
    -> Load Search 
    -> Load presentation ) 
    *if no verified or no loads = End Call*
-> Rate Negotiation : 
                    - If rejected = End call
                    - Starts counter: Within policy -> Continue
                                      No agreement -> End call
-> Booking
-> Senior Rep Handoff
-> Complete + Audit


# ARCHITECTURE PRINCIPLES

## 1- Deterministic controls around critical transactions 
 Business-critical decisions must not depend solely on LLM behavior
 The following controls are enforced outside the conversational model:

 - FMCSA eligibility
 - OTP verification
 - Load eligibility
 - Rate authorization
 - Maximum negotiation rounds
 - Booking authorization
 - TMS confirmation
 - Handoff eligibility

## 2- Secrets never enter the conversational context
The TMS max_rate is a protected business value

It is never:
- Included in the LLM prompt
- Returned to the conversational agent
- Spoken to the carrier
- Exposed through tool responses
- Returned through error messages

The policy engine evaluates proposed rates internally and returns only an allowed decision

For example:
{
  ¨desicion¨:¨ÇOUNTER¨
  ¨message¨: ¨the current offer is not acceptable. I can offer $1,850.¨
  }

The agent does not receive the underlying max_rate.

## 3- Verification is a hard gate

FMCSA verification alone does not authorize a carrier to receive loads.

A carrier must satisfy:
FMCSA authority = ACTIVE
AND
OTP verification = SUCCESFUL

before load matching can occur

## 4- LLM output is treated as untrusted input
Carrier speech and model-generated tool arguments are validated before privileged operations are executed.

The system does not allow conversational instructions to bypass:
- Authentication
- Authorization
- Negotiation limits
- Pricing controls
- Booking requiremnts

  ## 5- Reliability is part of the workflow
  The legacy TMS is expected to experience:
  - Timeouts
  - Malformed responses
  - High-load failures
 
  The integration therefore includes:
  - Timeouts
  - Bounded retries
  - Backoff
  - Response validation
  - Error normalization
  - Idempotency for booking operations
 
    # Technology Stack

    The prototype is designed to remain platform-agnostic during development.

    *Conversational AI*
    - HappyRobot
    - Function calling
    - Structured outputs
   

    *Backend*
    - Python
    - Deterministic workflow/state management
    - REST-style internal service interfaces where appropriate
   
    *Integrations*
    - FMCSA API
    - Legacy TMS via TCP socket / fixed- width protocol
    - Mock Senior Representative Queue
    - OTP service
   
    *Deployment*
    - Docker
    - Docker Compose for local development
    - Cloud deployment target TBD
   
    *Target Platform*
    - HappyRobot Voice Agent
    - HappyRobot Workflow
    - HappyRobot Twins
    - HappyRobot Apps
   
The final implementation will map the platform-agnostic components to HappyRobot capabilities once platform access is available

  # System Design

  The system is organized into several logical layers:

 1. [Conversational Agent] ->Understanding, Dialogue, Tools

 2. [Workflow / Orchestrator] -> State, routing, retries

 2.1 [Compliance Policy] ->FMCSA , OTP
 2.2 [Negotiation Policy] -> Rate, Rules
 2.3 [Booking Policy] -> TMS Integration

 # Known Prototype Limitations
- FMCSA currently uses a deterministic mock implementation.
- OTP verification currently uses a mock test code.
- The HappyRobot OTP delivery integration still needs final SMS/email wiring.
- The legacy TCP adapter is implemented but requires candidate-specific TMS hostname, port, and auth token for live validation.
- Senior-representative transfer is mocked because Web Call transfers are not supported.
- Docker files are complete but local execution is pending a required development-machine restart.
- The HappyRobot operational App currently uses the generated server-first template connected to Twin and can be further customized for richer KPI visualization.
  
   

