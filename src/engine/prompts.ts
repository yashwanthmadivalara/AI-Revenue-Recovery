export const HINGLISH_VOICE_SCRIPT_TEMPLATE = (params: {
  customer_name: string;
  company_name: string;
  currency: string;
  amount: number;
  days_overdue: number;
}) =>
  `Namaste ${params.customer_name} ji! Main ${params.company_name} ke accounts team se baat kar raha hoon. ` +
  `Aapka invoice amount of ${params.currency} ${params.amount} overdue chal raha hai for the last ${params.days_overdue} days. ` +
  `Kya koi billing mismatch ya issue tha jisme hum help kar sakte hain? ` +
  `Agar sab theek hai, toh kya hum aaj ya kal tak payment expect kar sakte hain? Can you provide a confirmed Promise-to-Pay date?`;

export const EMAIL_RECOVERY_TEMPLATES = {
  soft_decline: (params: {
    customer_name: string;
    currency: string;
    amount: number;
    retry_delay_hours: number;
    payment_link: string;
  }) => `Hi ${params.customer_name},

We noticed an issue processing your latest payment of ${params.currency} ${params.amount} for your subscription.
This often happens due to temporary bank limits or card security verification.

We will automatically retry processing in ${params.retry_delay_hours} hours. Alternatively, you can securely update your payment details here:
👉 ${params.payment_link}

Best regards,
Billing Team`,

  abandoned_checkout: (params: {
    customer_name: string;
    discount_pct: number;
    payment_link: string;
  }) => `Hi ${params.customer_name},

We noticed you left some great items in your cart! To help you complete your order, here is an exclusive ${params.discount_pct}% discount valid for the next 24 hours:

👉 Complete Your Order: ${params.payment_link}

If you had any questions or encountered any technical hiccups, simply reply to this email!

Warmly,
Customer Support`,

  overdue_invoice: (params: {
    customer_name: string;
    invoice_id: string;
    currency: string;
    amount: number;
    days_overdue: number;
    payment_link: string;
  }) => `Dear ${params.customer_name},

This is a reminder regarding Outstanding Invoice #${params.invoice_id} for ${params.currency} ${params.amount}, which is now ${params.days_overdue} days overdue.

Please access your secure enterprise payment portal to settle via Wire, Card, or UPI:
👉 Pay Invoice: ${params.payment_link}

If your accounts team has already scheduled this disbursement, please let us know the expected date so we can update your account ledger.

Sincerely,
Accounts Receivable Management`,
};
