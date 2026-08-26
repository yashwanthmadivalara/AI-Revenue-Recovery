"""
Prompt templates and dynamic message generators for AI Revenue Recovery.
Includes specialized prompts for Soft Declines, Abandoned Checkouts, Overdue B2B Receivables,
and Hinglish AI Voice Call scripts with Promise-to-Pay negotiation.
"""

DIAGNOSIS_SYSTEM_PROMPT = """You are an expert Financial Risk and AI Revenue Recovery Agent.
Your objective is to perform root-cause analysis on a failed revenue event and formulate the optimal, high-converting, compliant recovery strategy.

Input Details:
- Customer: {customer_name} ({customer_email})
- Amount at Risk: {amount} {currency}
- Risk Type: {risk_type}
- Event Metadata: {metadata}
- Language: {language}

You must return a structured JSON response with:
1. "root_cause": Clear explanation of the failure (e.g. Card velocity limit, Churn hesitation, Liquidity delay).
2. "confidence": A score between 0.1 and 1.0.
3. "recommended_channel": One of ["gateway_retry", "email", "sms", "voice", "invoice_portal", "manual_escalation"].
4. "strategy_summary": 1-2 sentences summarizing the tactical approach.
5. "subject": Relevant email or message subject line.
6. "message_body": Personalized copy (or Voice AI conversational prompt if voice channel).
7. "tone": E.g. "empathetic_supportive", "formal_ar", "conversational_hinglish", "urgent_preservation".
8. "retry_delay_hours": Integer hours if gateway_retry (e.g. 12, 24, 72).
9. "offered_discount_pct": Float discount if checkout abandonment (e.g. 5.0, 10.0).
10. "installment_eligible": True/False if high-ticket overdue invoice.
11. "reasoning_chain": Array of bullet points explaining your decision.
"""

HINGLISH_VOICE_SCRIPT_TEMPLATE = """Namaste {customer_name} ji! Main {company_name} ke accounts team se baat kar raha hoon. 
Aapka invoice amount of {currency} {amount} overdue chal raha hai for the last {days_overdue} days. 
Kya koi billing mismatch ya issue tha jisme hum help kar sakte hain? 
Agar sab theek hai, toh kya hum aaj ya kal tak payment expect kar sakte hain? Can you provide a confirmed Promise-to-Pay date?"""

EMAIL_RECOVERY_TEMPLATES = {
    "soft_decline": """Hi {customer_name},

We noticed an issue processing your latest payment of {currency} {amount} for your subscription.
This often happens due to temporary bank limits or card security verification.

We will automatically retry processing in {retry_delay_hours} hours. Alternatively, you can securely update your payment details here:
👉 {payment_link}

Best regards,
Billing Team""",

    "abandoned_checkout": """Hi {customer_name},

We noticed you left some great items in your cart! To help you complete your order, here is an exclusive {discount_pct}% discount valid for the next 24 hours:

👉 Complete Your Order: {payment_link}

If you had any questions or encountered any technical hiccups, simply reply to this email!

Warmly,
Customer Support""",

    "overdue_invoice": """Dear {customer_name},

This is a reminder regarding Outstanding Invoice #{invoice_id} for {currency} {amount}, which is now {days_overdue} days overdue.

Please access your secure enterprise payment portal to settle via Wire, Card, or UPI:
👉 Pay Invoice: {payment_link}

If your accounts team has already scheduled this disbursement, please let us know the expected date so we can update your account ledger.

Sincerely,
Accounts Receivable Management"""
}
