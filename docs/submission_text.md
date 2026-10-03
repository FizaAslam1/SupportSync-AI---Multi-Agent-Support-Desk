# Short description
A multi-agent AI support desk that classifies customer queries, answers from an FAQ knowledge base, and escalates complaints by creating tickets, automating support and cutting response time.

# Long description
SupportSync AI automatically handles incoming customer queries using three cooperating agents built in n8n with Google Gemini. Agent 1 classifies each query (billing, technical, complaint, general) with priority and sentiment. Agent 2 writes an accurate reply strictly from the company knowledge base in Google Sheets and emails it to the customer. Agent 3 escalates unresolved or high-priority complaints by creating a ticket in Google Sheets, alerting the support team by email and acknowledging the customer. Human agents focus only on complex cases while routine questions are answered in seconds.

# Tech stack
n8n, Google Gemini, Google Sheets, Gmail (WhatsApp optional)
